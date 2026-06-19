import logging
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoUsuario, ResultadoIntentoAcceso
from apps.accounts.services.attempt_service import record_login_attempt
from apps.accounts.services.session_service import create_user_session, hash_refresh_token
from apps.configuration.selectors.parametro_selectors import get_system_parameter_value
from apps.accounts.utils.log_utils import mask_email
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def authenticate_and_create_session(
    *,
    email: str,
    password: str,
    ip_address: str = None,
    user_agent: str = None
) -> tuple[str, str, Usuario]:
    """
    Verifies user credentials, handles temporal locks, creates active session,
    and returns JWT access and refresh tokens.
    """
    if not email:
        raise AuthenticationFailed("El correo electrónico es obligatorio")
        
    normalized_email = email.strip().lower()
    masked = mask_email(normalized_email)
    
    # 1. Search for user
    user = Usuario.objects.using('periodico_db').filter(usr_correo=normalized_email).first()
    
    if not user:
        logger.warning(f"Intento de inicio de sesión para correo inexistente: {masked}")
        # Run dummy check to prevent timing attacks
        Usuario().set_password(password)
        
        # Log failed attempt
        record_login_attempt(
            user=None,
            email_entered=normalized_email,
            resultado=ResultadoIntentoAcceso.CREDENCIALES_INVALIDAS,
            motivo="El correo ingresado no corresponde a ningun usuario",
            ip_address=ip_address,
            user_agent=user_agent
        )
        # Audit login failure
        AuditService.record_event(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.LOGIN_FALLIDO,
            entidad='usr_usuario',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Credenciales invalidas: correo inexistente",
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Login"
        )
        raise AuthenticationFailed("Credenciales inválidas.")

    # 2. Open atomic transaction and lock user row
    with transaction.atomic(using='periodico_db'):
        locked_user = Usuario.objects.using('periodico_db').select_for_update().get(pk=user.id)
        
        # Policy for deleted users (return generic response to prevent disclosure)
        if locked_user.eliminado:
            logger.warning(f"Intento de inicio de sesión para usuario eliminado: {masked}")
            locked_user.set_password(password) # timing safety
            record_login_attempt(
                user=locked_user,
                email_entered=normalized_email,
                resultado=ResultadoIntentoAcceso.CREDENCIALES_INVALIDAS,
                motivo="Usuario eliminado",
                ip_address=ip_address,
                user_agent=user_agent
            )
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.LOGIN_FALLIDO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Credenciales invalidas: usuario eliminado",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Login"
            )
            raise AuthenticationFailed("Credenciales inválidas.")
            
        # Check active lockouts
        if locked_user.bloqueado_hasta and locked_user.bloqueado_hasta > timezone.now():
            logger.warning(f"Intento de inicio de sesión para usuario bloqueado: {masked}")
            record_login_attempt(
                user=locked_user,
                email_entered=normalized_email,
                resultado=ResultadoIntentoAcceso.USUARIO_BLOQUEADO,
                motivo="Cuenta bloqueada temporalmente",
                ip_address=ip_address,
                user_agent=user_agent
            )
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.LOGIN_FALLIDO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Acceso denegado: cuenta bloqueada temporalmente",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Login"
            )
            raise AuthenticationFailed("La cuenta se encuentra bloqueada temporalmente.")

        # Check password correctness
        if not locked_user.check_password(password):
            logger.warning(f"Contraseña incorrecta para el usuario: {masked}")
            locked_user.intentos_fallidos += 1
            
            # Read max attempts from system parameters
            max_intentos = get_system_parameter_value('MAX_INTENTOS_LOGIN', 5)
            bloqueo_generado = False
            
            if locked_user.intentos_fallidos >= int(max_intentos):
                # Lock user for 15 minutes
                locked_user.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                bloqueo_generado = True
                logger.warning(f"Usuario {masked} ha sido bloqueado temporalmente por exceder intentos.")
                AuditService.record_event(
                    usuario=locked_user,
                    modulo=AuditoriaModulo.M02,
                    accion=AuditoriaAccion.CUENTA_BLOQUEADA,
                    entidad='usr_usuario',
                    entidad_id=str(locked_user.id),
                    resultado=AuditoriaResultado.RECHAZADO,
                    motivo="Límite de intentos fallidos alcanzado",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    proceso_origen="Auth Login"
                )

            locked_user.save(using='periodico_db')
            
            # Record failed attempt
            record_login_attempt(
                user=locked_user,
                email_entered=normalized_email,
                resultado=ResultadoIntentoAcceso.CREDENCIALES_INVALIDAS,
                motivo="Clave incorrecta",
                bloqueo_generado=bloqueo_generado,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.LOGIN_FALLIDO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Credenciales invalidas: clave incorrecta",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Login"
            )
            
            raise AuthenticationFailed("Credenciales inválidas.")

        # 3. Check active state and email verification
        if not locked_user.correo_verificado:
            logger.warning(f"Intento de ingreso sin verificar correo: {masked}")
            record_login_attempt(
                user=locked_user,
                email_entered=normalized_email,
                resultado=ResultadoIntentoAcceso.USUARIO_INACTIVO,
                motivo="Correo no verificado",
                ip_address=ip_address,
                user_agent=user_agent
            )
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.LOGIN_FALLIDO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo="Acceso denegado: correo pendiente de verificacion",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Login"
            )
            raise AuthenticationFailed("Su cuenta está pendiente de verificación de correo.")

        if locked_user.estado != EstadoUsuario.ACTIVO:
            logger.warning(f"Intento de ingreso de usuario inactivo/suspendido: {masked} (estado={locked_user.estado})")
            record_login_attempt(
                user=locked_user,
                email_entered=normalized_email,
                resultado=ResultadoIntentoAcceso.USUARIO_INACTIVO,
                motivo=f"Estado de cuenta: {locked_user.estado}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            AuditService.record_event(
                usuario=locked_user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.LOGIN_FALLIDO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=f"Acceso denegado: cuenta en estado {locked_user.estado}",
                ip_address=ip_address,
                user_agent=user_agent,
                proceso_origen="Auth Login"
            )
            raise AuthenticationFailed("Su cuenta se encuentra suspendida o inactiva.")

        # 4. Successful credentials verification. Reset attempts.
        locked_user.intentos_fallidos = 0
        locked_user.bloqueado_hasta = None
        locked_user.last_login = timezone.now()
        locked_user.save(using='periodico_db')

        # 5. Create Session inside transaction
        # First save with dummy hash to get the session object
        session = create_user_session(
            user=locked_user,
            plain_refresh_token="temp_refresh_token_to_be_replaced",
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 6. Generate SimpleJWT tokens with custom claims
        refresh = RefreshToken()
        refresh['session_id'] = str(session.id)
        refresh['user_id'] = locked_user.id
        
        access = refresh.access_token
        access['session_id'] = str(session.id)
        access['user_id'] = locked_user.id
        
        plain_refresh_str = str(refresh)
        plain_access_str = str(access)

        # Update session with the real refresh token hash
        session.token_hash = hash_refresh_token(plain_refresh_str)
        session.save(using='periodico_db')

        # 7. Record successful login attempt
        record_login_attempt(
            user=locked_user,
            email_entered=normalized_email,
            resultado=ResultadoIntentoAcceso.EXITOSO,
            motivo="Autenticacion exitosa",
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 8. Record audit log
        AuditService.record_event(
            usuario=locked_user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.LOGIN_EXITOSO,
            entidad='usr_usuario',
            entidad_id=str(locked_user.id),
            valores_nuevos={
                'ses_id': str(session.id),
                'usr_correo': masked
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen="Auth Login"
        )

    logger.info(f"Inicio de sesión exitoso y sesión creada para usuario {masked}.")
    return plain_access_str, plain_refresh_str, locked_user
