import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError, PermissionDenied
from apps.accounts.models.sesion import Sesion
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoSesion
from apps.accounts.services.session_service import hash_refresh_token
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def logout_user_session(
    *,
    user: Usuario,
    refresh_token_str: str,
    ip_address: str = None,
    user_agent: str = None
) -> None:
    """
    Revokes the session associated with the given refresh token by marking it as CERRADA.
    Keeps the operation idempotent and safe.
    """
    if not refresh_token_str:
        raise ValidationError({"refresh": "El token de actualización es obligatorio"})

    # 1. Hash refresh token to lookup session
    hashed_refresh = hash_refresh_token(refresh_token_str)
    
    try:
        session = Sesion.objects.using('periodico_db').get(token_hash=hashed_refresh)
    except Sesion.DoesNotExist:
        # Idempotency: if session already rotated or deleted, return success without revealing details
        logger.warning("Intento de logout con token inexistente o ya invalidado por rotación.")
        return

    # 2. Check ownership
    if session.usuario_id != user.id:
        logger.warning(f"Usuario {user.id} intentó cerrar sesión {session.id} del usuario {session.usuario_id}")
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.SESION_REVOCADA,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Intento de logout en sesion de otro usuario",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Logout"
        )
        raise PermissionDenied("No tiene permisos para cerrar esta sesión.")

    # 3. If session is already closed/revoked, return success quietly (idempotency)
    if session.estado != EstadoSesion.ACTIVA:
        logger.info(f"Sesión {session.id} ya se encontraba inactiva (estado={session.estado}). Completando silenciosamente.")
        return

    # 4. Atomic update to mark session closed
    with transaction.atomic(using='periodico_db'):
        locked_session = Sesion.objects.using('periodico_db').select_for_update().get(pk=session.id)
        
        if locked_session.estado == EstadoSesion.ACTIVA:
            locked_session.estado = EstadoSesion.CERRADA
            locked_session.fecha_cierre = timezone.now()
            locked_session.motivo_cierre = "Cierre de sesion voluntario"
            locked_session.save(using='periodico_db')
            
            # Record audit log
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.LOGOUT_EXITOSO,
                entidad='ses_sesion',
                entidad_id=str(locked_session.id),
                valores_nuevos={
                    'ses_id': str(locked_session.id),
                    'ses_estado': EstadoSesion.CERRADA
                },
                resultado=AuditoriaResultado.EXITOSO,
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Logout"
            )

    logger.info(f"Sesión {session.id} cerrada exitosamente para usuario {user.id}.")
