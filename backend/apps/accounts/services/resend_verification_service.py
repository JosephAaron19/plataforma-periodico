import logging
import uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.services.token_service import generate_verification_token
from apps.accounts.services.email_service import send_verification_email
from apps.accounts.utils.log_utils import mask_email
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def resend_verification_link(
    *,
    email: str,
    ip_address: str = None,
    user_agent: str = None
) -> None:
    """
    Handles secure resending of email verification link with rate limiting,
    atomic transactions, audit trail, and anti-enumeration protection.
    """
    if not email:
        logger.warning("Intento de reenvío de verificación sin correo.")
        return

    normalized_email = email.strip().lower()
    masked = mask_email(normalized_email)
    
    # 1. Look up user securely in the periodico_db connection
    user = Usuario.objects.using('periodico_db').filter(usr_correo=normalized_email).first()
    
    # 2. Record initial solicitation event
    # To protect privacy and prevent user enumeration:
    # - If user exists, log with user object.
    # - If user does not exist, log with usuario=None and minimal context (masked email).
    AuditService.record_event(
        usuario=user,
        modulo=AuditoriaModulo.M02,
        accion=AuditoriaAccion.REENVIO_VERIFICACION_SOLICITADO,
        entidad='ver_verificacion_correo',
        valores_nuevos={'usr_correo': masked},
        resultado=AuditoriaResultado.EXITOSO if user else AuditoriaResultado.RECHAZADO,
        ip_address=ip_address,
        user_agent=user_agent,
        proceso_origen="Reenvio de Verificacion"
    )

    # 3. Policy for non-existing users
    if not user:
        logger.info(f"Reenvío solicitado para correo no registrado: {masked}. Ignorando de forma silenciosa.")
        AuditService.record_event(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="El usuario no existe en el sistema",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Reenvio de Verificacion"
        )
        return

    # 4. Policy for active and verified users
    if user.estado == EstadoUsuario.ACTIVO and user.correo_verificado:
        logger.info(f"Reenvío solicitado para usuario ya ACTIVO y VERIFICADO: {masked}. Ignorando.")
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="El usuario ya se encuentra activo y verificado",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Reenvio de Verificacion"
        )
        return

    # 5. Policy for blocked, suspended, inactive, or deleted users
    # Verification email resend is ONLY allowed for non-deleted PENDIENTE users
    if user.eliminado or user.estado != EstadoUsuario.PENDIENTE:
        logger.warning(
            f"Reenvío solicitado para usuario inhabilitado o no PENDIENTE: {masked} "
            f"(estado={user.estado}, eliminado={user.eliminado}). Ignorando."
        )
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo=f"Estado de usuario no elegible para reenvio: estado={user.estado}, eliminado={user.eliminado}",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Reenvio de Verificacion"
        )
        return

    # 6. Apply frequency rate limiting
    now = timezone.now()
    
    # Check 1: Minimum interval of 60 seconds
    sixty_seconds_ago = now - timedelta(seconds=60)
    recent_exists = VerificacionCorreo.objects.using('periodico_db').filter(
        usuario=user,
        fecha_solicitud__gte=sixty_seconds_ago
    ).exists()
    
    if recent_exists:
        logger.warning(f"Límite de frecuencia de 60 segundos alcanzado para {masked}.")
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Intento de reenvio antes de los 60 segundos permitidos",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Reenvio de Verificacion"
        )
        return

    # Check 2: Maximum of 5 requests within 24 hours
    twenty_four_hours_ago = now - timedelta(hours=24)
    daily_count = VerificacionCorreo.objects.using('periodico_db').filter(
        usuario=user,
        fecha_solicitud__gte=twenty_four_hours_ago
    ).count()
    
    if daily_count >= 5:
        logger.warning(f"Límite de 5 solicitudes en 24 horas superado para {masked}.")
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Exceso de solicitudes de reenvio de verificacion en 24 horas",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Reenvio de Verificacion"
        )
        return

    # 7. Execute atomic transaction with database locking
    with transaction.atomic(using='periodico_db'):
        # Controlled lock on user record to prevent race conditions
        locked_user = Usuario.objects.using('periodico_db').select_for_update().get(pk=user.id)
        
        # Double-check constraints inside lock context
        # Re-verify 60 seconds check
        if VerificacionCorreo.objects.using('periodico_db').filter(usuario=locked_user, fecha_solicitud__gte=timezone.now() - timedelta(seconds=60)).exists():
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
                entidad='ver_verificacion_correo',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Intento de reenvio antes de los 60 segundos permitidos (concurrencia)",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Reenvio de Verificacion"
            )
            return

        # Re-verify 24 hours check
        if VerificacionCorreo.objects.using('periodico_db').filter(usuario=locked_user, fecha_solicitud__gte=timezone.now() - timedelta(hours=24)).count() >= 5:
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
                entidad='ver_verificacion_correo',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Exceso de solicitudes de reenvio de verificacion en 24 horas (concurrencia)",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Reenvio de Verificacion"
            )
            return

        # Invalidate previous pending verification tokens
        VerificacionCorreo.objects.using('periodico_db').filter(
            usuario=locked_user,
            estado=EstadoVerificacion.PENDIENTE
        ).update(
            estado=EstadoVerificacion.INVALIDADA,
            motivo_invalidacion="Reenvío de enlace de verificación solicitado"
        )
        
        # Generate new verification token
        plain_token, hashed_token, expires_at = generate_verification_token()
        
        # Store only its hash
        verification = VerificacionCorreo(
            id=uuid.uuid4(),
            usuario=locked_user,
            token_hash=hashed_token,
            fecha_expiracion=expires_at,
            estado=EstadoVerificacion.PENDIENTE,
            direccion_ip=ip_address,
            intentos=0
        )
        verification.save(using='periodico_db')
        
        # Record audit event: REENVIO_VERIFICACION_ENVIADO
        AuditService.record_event(
            usuario=locked_user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_ENVIADO,
            entidad='ver_verificacion_correo',
            entidad_id=str(verification.id),
            valores_nuevos={
                'ver_id': str(verification.id),
                'ver_estado': EstadoVerificacion.PENDIENTE,
                're_envio': True
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Reenvio de Verificacion"
        )
        
        # Queue Celery task ONLY after the transaction commits successfully
        transaction.on_commit(
            lambda: send_verification_email(
                email=locked_user.usr_correo,
                nombres=locked_user.nombres,
                plain_token=plain_token
            ),
            using='periodico_db'
        )

    logger.info(f"Reenvío de verificación procesado exitosamente para {masked}.")
