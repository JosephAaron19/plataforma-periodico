import logging
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from apps.accounts.models.sesion import Sesion
from apps.accounts.constants import EstadoSesion, EstadoUsuario
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class SafeJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1. Use SimpleJWT parent authentication to extract user & validate cryptographic token signature/expiration
        auth_result = super().authenticate(request)
        if auth_result is None:
            return None
            
        user, validated_token = auth_result
        
        # Extract IP and User Agent from request
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # 2. Check user status
        if not user or user.eliminado:
            raise AuthenticationFailed("El usuario asociado a este token ha sido eliminado")
            
        if user.estado != EstadoUsuario.ACTIVO or not user.correo_verificado:
            raise AuthenticationFailed("La cuenta de usuario no está activa o no ha sido verificada")

        # 3. Retrieve session_id
        session_id = validated_token.get('session_id')
        if not session_id:
            logger.warning(f"Intento de acceso con token sin claim session_id para usuario {user.id}")
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.ACCESO_CON_SESION_INVALIDA,
                entidad='ses_sesion',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Token no contiene claim session_id",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="SafeJWTAuthentication"
            )
            raise InvalidToken("El token de acceso no contiene una sesión válida")

        # 4. Look up session in database
        try:
            session = Sesion.objects.using('periodico_db').get(pk=session_id)
        except Sesion.DoesNotExist:
            logger.warning(f"Sesión {session_id} no encontrada en base de datos para usuario {user.id}")
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.ACCESO_CON_SESION_INVALIDA,
                entidad='ses_sesion',
                entidad_id=str(session_id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Sesion inexistente en base de datos",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="SafeJWTAuthentication"
            )
            raise InvalidToken("La sesión no existe")

        # 5. Validate session state
        is_invalid = (
            session.estado != EstadoSesion.ACTIVA or
            session.fecha_cierre is not None or
            session.fecha_expiracion < timezone.now()
        )
        
        if is_invalid:
            logger.warning(f"Intento de acceso con sesión inválida: ID={session.id}, Estado={session.estado}, Cierre={session.fecha_cierre}")
            AuditService.record_event(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.ACCESO_CON_SESION_INVALIDA,
                entidad='ses_sesion',
                entidad_id=str(session.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=f"Sesion invalida. Estado: {session.estado}, Cerrada: {session.fecha_cierre is not None}, Expirada: {session.fecha_expiracion < timezone.now()}",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="SafeJWTAuthentication"
            )
            raise InvalidToken("La sesión ha expirado, ha sido cerrada o revocada")

        return user, validated_token
