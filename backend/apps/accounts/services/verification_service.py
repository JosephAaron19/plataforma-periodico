import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.services.token_service import hash_token
from apps.accounts.utils.log_utils import mask_email

logger = logging.getLogger(__name__)

def verify_email(plain_token: str, ip_address: str = None) -> VerificacionCorreo:
    """
    Verifies a plain token, validates integrity, handles constraints,
    updates attempt logs, and activates the user account safely.
    """
    if not plain_token:
        raise ValidationError({"token": "El token de verificación es obligatorio"})
        
    hashed_token = hash_token(plain_token)
    
    try:
        verification = VerificacionCorreo.objects.using('periodico_db').select_related('usuario').get(token_hash=hashed_token)
    except VerificacionCorreo.DoesNotExist:
        logger.warning(f"Intento de verificación con token inválido desde IP: {ip_address}")
        raise ValidationError({"token": "El token de verificación es inválido o no existe"})

    user = verification.usuario
    masked = mask_email(user.usr_correo)

    # Begin atomic transaction on periodico_db connection
    with transaction.atomic(using='periodico_db'):
        # 1. Increment attempts counter
        verification.intentos += 1
        
        # 2. Check if user is suspended, inactive, blocked, or deleted
        if user.eliminado or user.estado in (EstadoUsuario.BLOQUEADO, EstadoUsuario.SUSPENDIDO, EstadoUsuario.INACTIVO):
            verification.save(using='periodico_db')
            logger.warning(f"Intento de verificar usuario inhabilitado ({user.estado}, eliminado={user.eliminado}) para {masked}")
            raise ValidationError({"token": "El usuario asociado a esta cuenta se encuentra bloqueado, suspendido o inactivo"})
        
        # 3. Check if already verified
        if verification.estado == EstadoVerificacion.VERIFICADA or verification.fecha_verificacion is not None:
            verification.save(using='periodico_db')
            raise ValidationError({"token": "El correo ya ha sido verificado anteriormente"})
            
        # 4. Check if invalidated
        if verification.estado == EstadoVerificacion.INVALIDADA:
            verification.save(using='periodico_db')
            raise ValidationError({"token": "El token de verificación no es válido o ha sido anulado"})
            
        # 5. Check if expired
        if verification.estado == EstadoVerificacion.VENCIDA or verification.fecha_expiracion < timezone.now():
            verification.estado = EstadoVerificacion.VENCIDA
            verification.save(using='periodico_db')
            raise ValidationError({"token": "El enlace de verificación ha expirado"})
            
        # 6. Limit attempts to prevent brute-forcing
        if verification.intentos > 5:
            verification.estado = EstadoVerificacion.INVALIDADA
            verification.motivo_invalidacion = "Exceso de intentos de verificación"
            verification.save(using='periodico_db')
            logger.warning(f"Token invalidado por exceso de intentos para {masked}")
            raise ValidationError({"token": "Token bloqueado por exceso de intentos fallidos"})
            
        # 7. Mark verification as success
        verification.estado = EstadoVerificacion.VERIFICADA
        verification.fecha_verificacion = timezone.now()
        verification.direccion_ip = ip_address or verification.direccion_ip
        verification.save(using='periodico_db')
        
        # 8. Activate User
        user.estado = EstadoUsuario.ACTIVO
        user.correo_verificado = True
        user.fecha_verificacion = timezone.now()
        user.save(using='periodico_db')
        
        # 9. Invalidate any other pending verification tokens for this user
        VerificacionCorreo.objects.using('periodico_db').filter(
            usuario=user,
            estado=EstadoVerificacion.PENDIENTE
        ).exclude(id=verification.id).update(
            estado=EstadoVerificacion.INVALIDADA,
            motivo_invalidacion="Verificación exitosa completada en otro token"
        )
        
        logger.info(f"Usuario verificado y activado exitosamente: {masked}")
        
    return verification
