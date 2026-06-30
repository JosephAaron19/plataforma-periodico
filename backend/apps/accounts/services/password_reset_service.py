import uuid
import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models.usuario import Usuario
from apps.accounts.models.recuperacion import RecuperacionCuenta
from apps.accounts.constants import EstadoUsuario, EstadoRecuperacion
from apps.accounts.services.token_service import generate_recovery_token, hash_token
from apps.accounts.services.email_service import send_password_reset_email
from apps.accounts.utils.log_utils import mask_email
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def request_password_reset(*, email: str, ip_address: str = None, user_agent: str = None) -> bool:
    """
    Handles a password reset request. Returns True if the user exists, False otherwise.
    """
    if not email:
        raise ValidationError({"email": "El correo electrónico es obligatorio"})
    
    normalized_email = email.strip().lower()
    masked = mask_email(normalized_email)
    
    user = Usuario.objects.using('periodico_db').filter(usr_correo=normalized_email).first()
    
    if not user:
        logger.info(f"Solicitud de restablecimiento para correo no registrado: {masked}")
        return False

    with transaction.atomic(using='periodico_db'):
        # Invalidate previous requests
        RecuperacionCuenta.objects.using('periodico_db').filter(
            usuario=user,
            estado__in=[EstadoRecuperacion.SOLICITADA, EstadoRecuperacion.ENVIADA]
        ).update(
            estado=EstadoRecuperacion.INVALIDADA,
            motivo_invalidacion="Nueva solicitud de restablecimiento"
        )
        
        # Generate token
        plain_token, hashed_token, expires_at = generate_recovery_token()
        
        recovery = RecuperacionCuenta(
            id=uuid.uuid4(),
            usuario=user,
            token_hash=hashed_token,
            fecha_expiracion=expires_at,
            ip_solicitud=ip_address,
            intentos=0,
            estado=EstadoRecuperacion.ENVIADA
        )
        recovery.save(using='periodico_db')
        
        # Audit Solicitud
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.SOLICITUD_RECUPERACION_CLAVE,
            entidad='rec_recuperacion_cuenta',
            entidad_id=str(recovery.id),
            valores_anteriores=None,
            valores_nuevos={
                'usr_correo': normalized_email,
                'rec_estado': EstadoRecuperacion.ENVIADA
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Recuperacion Clave Solicitud"
        )
        
        # Schedule email Celery task
        transaction.on_commit(
            lambda: send_password_reset_email(
                email=user.usr_correo,
                nombres=user.nombres,
                plain_token=plain_token
            ),
            using='periodico_db'
        )
        
    logger.info(f"Solicitud de restablecimiento registrada exitosamente para: {masked}")
    return True

def confirm_password_reset(*, plain_token: str, password: str, ip_address: str = None, user_agent: str = None) -> None:
    """
    Confirms a password reset, validating the token and updating the user password.
    """
    if not plain_token:
        raise ValidationError({"token": "El token de recuperación es obligatorio"})
    if not password:
        raise ValidationError({"password": "La contraseña es obligatoria"})
        
    hashed_token = hash_token(plain_token)
    
    try:
        recovery = RecuperacionCuenta.objects.using('periodico_db').select_related('usuario').get(token_hash=hashed_token)
    except RecuperacionCuenta.DoesNotExist:
        logger.warning(f"Intento de restablecimiento con token inválido desde IP: {ip_address}")
        AuditService.record_event(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.RECUPERACION_CLAVE_FALLIDA,
            entidad='rec_recuperacion_cuenta',
            entidad_id=None,
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="El token de recuperacion es invalido o no existe",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Recuperacion Clave Confirmacion"
        )
        raise ValidationError({"token": "El token de recuperación es inválido o no existe"})
        
    user = recovery.usuario
    masked = mask_email(user.usr_correo)
    
    with transaction.atomic(using='periodico_db'):
        recovery.intentos += 1
        
        # Security checks
        if user.eliminado or user.estado in (EstadoUsuario.BLOQUEADO, EstadoUsuario.SUSPENDIDO):
            recovery.save(using='periodico_db')
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.RECUPERACION_CLAVE_FALLIDA,
                entidad='rec_recuperacion_cuenta',
                entidad_id=str(recovery.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=f"Usuario inhabilitado: estado={user.estado}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise ValidationError({"token": "El usuario asociado a esta cuenta se encuentra bloqueado o suspendido"})
            
        if recovery.estado == EstadoRecuperacion.UTILIZADA or recovery.fecha_uso is not None:
            recovery.save(using='periodico_db')
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.RECUPERACION_CLAVE_FALLIDA,
                entidad='rec_recuperacion_cuenta',
                entidad_id=str(recovery.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="El token de recuperacion ya fue utilizado",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise ValidationError({"token": "El enlace de recuperación ya ha sido utilizado"})
            
        if recovery.estado == EstadoRecuperacion.INVALIDADA:
            recovery.save(using='periodico_db')
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.RECUPERACION_CLAVE_FALLIDA,
                entidad='rec_recuperacion_cuenta',
                entidad_id=str(recovery.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=f"Token anulado: {recovery.motivo_invalidacion}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise ValidationError({"token": "El token de recuperación no es válido o ha sido anulado"})
            
        if recovery.estado == EstadoRecuperacion.VENCIDA or recovery.fecha_expiracion < timezone.now():
            recovery.estado = EstadoRecuperacion.VENCIDA
            recovery.save(using='periodico_db')
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.RECUPERACION_CLAVE_FALLIDA,
                entidad='rec_recuperacion_cuenta',
                entidad_id=str(recovery.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="El token de recuperacion ha expirado",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise ValidationError({"token": "El enlace de recuperación ha expirado"})
            
        if recovery.intentos > 5:
            recovery.estado = EstadoRecuperacion.INVALIDADA
            recovery.motivo_invalidacion = "Exceso de intentos de recuperación"
            recovery.save(using='periodico_db')
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.RECUPERACION_CLAVE_FALLIDA,
                entidad='rec_recuperacion_cuenta',
                entidad_id=str(recovery.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Token bloqueado por exceso de intentos fallidos",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise ValidationError({"token": "Token bloqueado por exceso de intentos fallidos"})
            
        # Update Password
        user.set_password(password)
        user.save(using='periodico_db')
        
        # Mark recovery as success
        recovery.estado = EstadoRecuperacion.UTILIZADA
        recovery.fecha_uso = timezone.now()
        recovery.save(using='periodico_db')
        
        # Invalidate any other pending requests for this user
        RecuperacionCuenta.objects.using('periodico_db').filter(
            usuario=user,
            estado__in=[EstadoRecuperacion.SOLICITADA, EstadoRecuperacion.ENVIADA]
        ).exclude(id=recovery.id).update(
            estado=EstadoRecuperacion.INVALIDADA,
            motivo_invalidacion="Restablecimiento completado en otro token"
        )
        
        # Audit successful password reset
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.RECUPERACION_CLAVE_EXITOSA,
            entidad='usr_usuario',
            entidad_id=str(user.id),
            valores_anteriores=None,
            valores_nuevos={'usr_password_updated': True},
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Contraseña restablecida exitosamente para: {masked}")
