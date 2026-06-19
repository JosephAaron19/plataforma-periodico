import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.accounts.models.sesion import Sesion
from apps.accounts.constants import EstadoSesion, EstadoUsuario
from apps.accounts.services.session_service import hash_refresh_token
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def refresh_user_tokens(
    *,
    refresh_token_str: str,
    ip_address: str = None,
    user_agent: str = None
) -> tuple[str, str]:
    """
    Validates a refresh token, ensures the corresponding session is active in
    pdg.ses_sesion, rotates the refresh token, and returns new access/refresh tokens.
    """
    if not refresh_token_str:
        raise AuthenticationFailed("El token de actualización es obligatorio")

    # 1. Cryptographically validate the refresh token
    try:
        token_obj = RefreshToken(refresh_token_str)
    except TokenError as e:
        logger.warning(f"Fallo de validación criptográfica de refresh token: {e}")
        AuditService.record_event(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo=f"Token de actualización invalido: {str(e)}",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Refresh"
        )
        raise AuthenticationFailed("Token de actualización inválido o expirado.")

    # 2. Extract session_id and user_id claims
    session_id = token_obj.get('session_id')
    user_id = token_obj.get('user_id')
    
    if not session_id or not user_id:
        logger.warning("Intento de refresh con token sin claims session_id o user_id")
        AuditService.record_event(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Token no contiene session_id o user_id",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Refresh"
        )
        raise AuthenticationFailed("Token de actualización inválido o incompleto.")

    # 3. Look up session in periodico_db by the hash of the incoming old refresh token
    hashed_old_refresh = hash_refresh_token(refresh_token_str)
    try:
        session = Sesion.objects.using('periodico_db').select_related('usuario').get(token_hash=hashed_old_refresh)
    except Sesion.DoesNotExist:
        logger.warning(f"Sesión con token_hash no encontrada en base de datos. Posible intento de reutilización.")
        AuditService.record_event(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Sesion no encontrada (posible reutilizacion o manipulacion de token)",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Refresh"
        )
        raise AuthenticationFailed("La sesión asociada al token no es válida o ha sido revocada.")

    user = session.usuario

    # 4. Check user status
    if user.eliminado or user.estado != EstadoUsuario.ACTIVO:
        logger.warning(f"Intento de refresh para usuario inhabilitado: {user.id}")
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            resultado=AuditoriaResultado.RECHAZADO,
            motivo=f"Usuario inhabilitado: estado={user.estado}, eliminado={user.eliminado}",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Refresh"
        )
        raise AuthenticationFailed("El usuario asociado a esta sesión se encuentra inhabilitado.")

    # 5. Validate session state
    is_invalid = (
        session.estado != EstadoSesion.ACTIVA or
        session.fecha_cierre is not None or
        session.fecha_expiracion < timezone.now() or
        str(session.id) != str(session_id)
    )

    if is_invalid:
        logger.warning(f"Intento de refresh en sesión inactiva/expirada: {session_id}")
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            resultado=AuditoriaResultado.RECHAZADO,
            motivo=f"Sesion inactiva o expirada: estado={session.estado}, expirada={session.fecha_expiracion < timezone.now()}",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Refresh"
        )
        raise AuthenticationFailed("La sesión asociada al token ha expirado, ha sido cerrada o revocada.")

    # 6. Execute atomic transaction to rotate refresh token in session
    with transaction.atomic(using='periodico_db'):
        # Lock session row
        locked_session = Sesion.objects.using('periodico_db').select_for_update().get(pk=session.id)
        
        # Double check inside lock
        if locked_session.token_hash != hashed_old_refresh:
            locked_session.estado = EstadoSesion.REVOCADA
            locked_session.fecha_cierre = timezone.now()
            locked_session.motivo_cierre = "Reutilizacion de refresh token detectada"
            locked_session.save(using='periodico_db')
            
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
                entidad='ses_sesion',
                entidad_id=str(locked_session.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Reutilizacion de refresh token (sesion revocada)",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Refresh"
            )
            raise AuthenticationFailed("La sesión asociada al token no es válida o ha sido revocada.")

        if locked_session.estado != EstadoSesion.ACTIVA or locked_session.fecha_expiracion < timezone.now():
            raise AuthenticationFailed("La sesión ya no está activa.")

        # Generate rotated tokens
        new_refresh = RefreshToken()
        new_refresh['session_id'] = str(locked_session.id)
        new_refresh['user_id'] = user.id
        
        new_access = new_refresh.access_token
        new_access['session_id'] = str(locked_session.id)
        new_access['user_id'] = user.id
        
        plain_refresh_str = str(new_refresh)
        plain_access_str = str(new_access)
        
        # Save new hash in DB (effectively invalidating the old refresh token)
        locked_session.token_hash = hash_refresh_token(plain_refresh_str)
        locked_session.fecha_ultimo_uso = timezone.now()
        locked_session.save(using='periodico_db')

        # Audit successful refresh
        AuditService.record_event(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_EXITOSO,
            entidad='ses_sesion',
            entidad_id=str(locked_session.id),
            valores_nuevos={
                'ses_id': str(locked_session.id),
                're_rotado': True
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Refresh"
        )

    logger.info(f"Rotación de refresh token exitosa para sesión {locked_session.id} (usuario {user.id}).")
    return plain_access_str, plain_refresh_str
