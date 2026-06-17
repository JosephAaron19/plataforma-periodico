import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.services.token_service import hash_token

logger = logging.getLogger(__name__)

def verify_email(plain_token: str, ip_address: str = None) -> VerificacionCorreo:
    """
    Verifies a plain token, validates its integrity and expiry, increments attempts,
    and activates the corresponding user account.
    """
    if not plain_token:
        raise ValidationError({"token": "El token de verificación es obligatorio"})
        
    hashed_token = hash_token(plain_token)
    
    try:
        verification = VerificacionCorreo.objects.select_related('usuario').get(token_hash=hashed_token)
    except VerificacionCorreo.DoesNotExist:
        logger.warning(f"Intento de verificación con token inválido desde IP: {ip_address}")
        raise ValidationError({"token": "El token de verificación es inválido o no existe"})

    # Begin atomic transaction to update attempts and state
    with transaction.atomic(using='periodico_db'):
        # 1. Increment attempts counter
        verification.intentos += 1
        
        # 2. Check if already verified
        if verification.estado == EstadoVerificacion.VERIFICADA or verification.fecha_verificacion is not None:
            verification.save(using='periodico_db')
            raise ValidationError({"token": "El correo ya ha sido verificado anteriormente"})
            
        # 3. Check if invalidated
        if verification.estado == EstadoVerificacion.INVALIDADA:
            verification.save(using='periodico_db')
            raise ValidationError({"token": "El token de verificación no es válido o ha sido anulado"})
            
        # 4. Check if expired
        if verification.estado == EstadoVerificacion.VENCIDA or verification.fecha_expiracion < timezone.now():
            verification.estado = EstadoVerificacion.VENCIDA
            verification.save(using='periodico_db')
            raise ValidationError({"token": "El enlace de verificación ha expirado"})
            
        # 5. Limit attempts to prevent brute-forcing
        if verification.intentos > 5:
            verification.estado = EstadoVerificacion.INVALIDADA
            verification.motivo_invalidacion = "Exceso de intentos de verificación"
            verification.save(using='periodico_db')
            logger.warning(f"Token {verification.id} invalidado por exceso de intentos")
            raise ValidationError({"token": "Token bloqueado por exceso de intentos fallidos"})
            
        # 6. Mark verification as success
        verification.estado = EstadoVerificacion.VERIFICADA
        verification.fecha_verificacion = timezone.now()
        verification.direccion_ip = ip_address or verification.direccion_ip
        verification.save(using='periodico_db')
        
        # 7. Activate User
        user = verification.usuario
        user.estado = EstadoUsuario.ACTIVO
        user.correo_verificado = True
        user.fecha_verificacion = timezone.now()
        user.save(using='periodico_db')
        
        logger.info(f"Usuario {user.id} ({user.usr_correo}) verificado y activado exitosamente")
        
    return verification
