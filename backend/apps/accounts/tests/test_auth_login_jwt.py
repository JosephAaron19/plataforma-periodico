from django.test import SimpleTestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock, ANY
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.sesion import Sesion
from apps.accounts.models.intento_acceso import IntentoAcceso
from apps.accounts.constants import EstadoUsuario, EstadoSesion, ResultadoIntentoAcceso
from apps.accounts.views.login import LoginView
from apps.accounts.views.refresh import TokenRefreshView
from apps.accounts.views.logout import LogoutView
from apps.accounts.authentication.jwt_authentication import SafeJWTAuthentication
from apps.accounts.services.login_service import authenticate_and_create_session
from apps.accounts.services.refresh_service import refresh_user_tokens
from apps.accounts.services.logout_service import logout_user_session
from apps.accounts.services.session_service import hash_refresh_token
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
import uuid

class DummyAtomic:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

@patch('django.db.transaction.atomic', DummyAtomic)
class AuthLoginJWTSecureTest(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        
        # Patch audit service to prevent database writes
        self.audit_patcher = patch('apps.audit.services.audit_service.AuditService.record_event')
        self.mock_record_event = self.audit_patcher.start()

    def tearDown(self):
        self.audit_patcher.stop()
        super().tearDown()

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.sesion.Sesion.save')
    @patch('apps.accounts.models.usuario.Usuario.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_exitoso(self, mock_user_using, mock_user_save, mock_session_save, mock_attempt_save):
        """
        Scenario: Active, verified user provides correct credentials.
        Response: 200 OK with tokens and user details.
        Database: Session created in pdg.ses_sesion. Attempts reset. Attempt logged.
        Audit: LOGIN_EXITOSO.
        """
        user = Usuario(id=1, usr_correo="user@example.com", nombres="John", apellidos="Doe", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "user@example.com", "password": "correctpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "user@example.com")
        self.assertEqual(response.data["user"]["nombres"], "John")

        # Verify DB calls
        self.assertEqual(user.intentos_fallidos, 0)
        self.assertIsNone(user.bloqueado_hasta)
        mock_user_save.assert_called_once()
        self.assertTrue(mock_session_save.called)
        self.assertTrue(mock_attempt_save.called)

        # Verify audits
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.LOGIN_EXITOSO,
            entidad='usr_usuario',
            entidad_id='1',
            valores_nuevos=ANY,
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Login"
        )

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_correo_inexistente(self, mock_user_using, mock_attempt_save):
        """
        Scenario: Email does not exist.
        Response: 401 Unauthorized with generic message.
        Audit: LOGIN_FALLIDO.
        """
        mock_user_using.return_value.filter.return_value.first.return_value = None

        request = self.factory.post('/api/v1/auth/login/', {"email": "noexiste@example.com", "password": "anypassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Credenciales inválidas.")
        self.assertTrue(mock_attempt_save.called)
        
        self.mock_record_event.assert_any_call(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.LOGIN_FALLIDO,
            entidad='usr_usuario',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Credenciales invalidas: correo inexistente",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Login"
        )

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_contrasena_incorrecta(self, mock_user_using, mock_user_save, mock_attempt_save):
        """
        Scenario: User exists but password is correct.
        Response: 401 Unauthorized with generic message.
        Database: Increments attempts.
        Audit: LOGIN_FALLIDO.
        """
        user = Usuario(id=1, usr_correo="user@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True, intentos_fallidos=0)
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "user@example.com", "password": "wrongpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Credenciales inválidas.")
        
        self.assertEqual(user.intentos_fallidos, 1)
        mock_user_save.assert_called_once()
        self.assertTrue(mock_attempt_save.called)

        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.LOGIN_FALLIDO,
            entidad='usr_usuario',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Credenciales invalidas: clave incorrecta",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Login"
        )

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_bloqueo_al_alcanzar_maximo(self, mock_user_using, mock_user_save, mock_attempt_save):
        """
        Scenario: User reaches 5 failed attempts.
        Response: 401 Unauthorized.
        Database: sets lock.
        Audit: CUENTA_BLOQUEADA and LOGIN_FALLIDO.
        """
        user = Usuario(id=1, usr_correo="user@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True, intentos_fallidos=4)
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "user@example.com", "password": "wrongpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(user.intentos_fallidos, 5)
        self.assertIsNotNone(user.bloqueado_hasta)
        self.assertTrue(user.bloqueado_hasta > timezone.now())
        
        mock_user_save.assert_called_once()
        
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.CUENTA_BLOQUEADA,
            entidad='usr_usuario',
            entidad_id='1',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Límite de intentos fallidos alcanzado",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Login"
        )

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_bloqueo_temporal_vigente(self, mock_user_using, mock_attempt_save):
        """
        Scenario: Locked out user tries to authenticate.
        Response: 401 Unauthorized with custom message.
        """
        user = Usuario(id=1, usr_correo="user@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True, bloqueado_hasta=timezone.now() + timedelta(minutes=10))
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "user@example.com", "password": "correctpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "La cuenta se encuentra bloqueada temporalmente.")

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_usuario_pendiente(self, mock_user_using, mock_attempt_save):
        """
        Scenario: Pending (unverified) user provides correct password.
        Response: 401 Unauthorized with custom message.
        """
        user = Usuario(id=1, usr_correo="pending@example.com", estado=EstadoUsuario.PENDIENTE, correo_verificado=False)
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "pending@example.com", "password": "correctpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Su cuenta está pendiente de verificación de correo.")

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_usuario_suspendido(self, mock_user_using, mock_attempt_save):
        """
        Scenario: Suspended user provides correct password.
        Response: 401 Unauthorized with custom message.
        """
        user = Usuario(id=1, usr_correo="suspend@example.com", estado=EstadoUsuario.SUSPENDIDO, correo_verificado=True)
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "suspend@example.com", "password": "correctpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Su cuenta se encuentra suspendida o inactiva.")

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_login_usuario_eliminado(self, mock_user_using, mock_attempt_save):
        """
        Scenario: Deleted user provides correct password.
        Response: 401 Unauthorized with generic message (anti-enumeration).
        """
        user = Usuario(id=1, usr_correo="deleted@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True, eliminado=True)
        user.set_password("correctpassword")
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        request = self.factory.post('/api/v1/auth/login/', {"email": "deleted@example.com", "password": "correctpassword"}, format='json')
        view = LoginView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Credenciales inválidas.")

    @patch('apps.accounts.models.sesion.Sesion.save')
    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_refresh_token_exitoso(self, mock_user_using, mock_session_using, mock_session_save):
        """
        Scenario: Rotate valid refresh token.
        Database: Session token_hash updated with new hash.
        Audit: TOKEN_REFRESH_EXITOSO.
        """
        user = Usuario(id=1, usr_correo="refresh@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user,
            fecha_expiracion=timezone.now() + timedelta(days=1),
            estado=EstadoSesion.ACTIVA
        )
        
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_session_using.return_value.select_related.return_value.get.return_value = session
        mock_session_using.return_value.select_for_update.return_value.get.return_value = session

        # Generate a real token to send
        refresh = RefreshToken()
        refresh['session_id'] = str(session.id)
        refresh['user_id'] = user.id
        refresh_str = str(refresh)
        
        # Configure lookup
        session.token_hash = hash_refresh_token(refresh_str)

        request = self.factory.post('/api/v1/auth/token/refresh/', {"refresh": refresh_str}, format='json')
        view = TokenRefreshView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        
        mock_session_save.assert_called_once()
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_EXITOSO,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            valores_nuevos=ANY,
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Refresh"
        )

    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    def test_refresh_token_invalido(self, mock_session_using):
        """
        Scenario: Try to refresh an invalid string.
        Response: 401 Unauthorized.
        Audit: TOKEN_REFRESH_RECHAZADO.
        """
        request = self.factory.post('/api/v1/auth/token/refresh/', {"refresh": "invalidtokenstring"}, format='json')
        view = TokenRefreshView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.mock_record_event.assert_any_call(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo=ANY,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Refresh"
        )

    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    def test_refresh_token_sesion_revocada(self, mock_session_using):
        """
        Scenario: Try to refresh a revoked session.
        Response: 401 Unauthorized.
        Audit: TOKEN_REFRESH_RECHAZADO.
        """
        user = Usuario(id=1, usr_correo="refresh@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user,
            fecha_expiracion=timezone.now() + timedelta(days=1),
            estado=EstadoSesion.REVOCADA,  # Revoked!
            fecha_cierre=timezone.now()
        )
        
        mock_session_using.return_value.select_related.return_value.get.return_value = session

        refresh = RefreshToken()
        refresh['session_id'] = str(session.id)
        refresh['user_id'] = user.id
        refresh_str = str(refresh)

        request = self.factory.post('/api/v1/auth/token/refresh/', {"refresh": refresh_str}, format='json')
        view = TokenRefreshView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.TOKEN_REFRESH_RECHAZADO,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            resultado=AuditoriaResultado.RECHAZADO,
            motivo=ANY,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Refresh"
        )

    @patch('apps.accounts.models.sesion.Sesion.save')
    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    def test_logout_exitoso(self, mock_session_using, mock_session_save):
        """
        Scenario: Authenticated user revokes session.
        Response: 200 OK.
        Audit: LOGOUT_EXITOSO.
        """
        user = Usuario(id=1, usr_correo="logout@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user,
            estado=EstadoSesion.ACTIVA
        )
        
        # Configure mocks
        mock_session_using.return_value.get.return_value = session
        mock_session_using.return_value.select_for_update.return_value.get.return_value = session

        refresh_str = "anyrefreshstring"

        request = self.factory.post('/api/v1/auth/logout/', {"refresh": refresh_str}, format='json')
        force_authenticate(request, user=user)
        view = LogoutView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(session.estado, EstadoSesion.CERRADA)
        mock_session_save.assert_called_once()

        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.LOGOUT_EXITOSO,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            valores_nuevos=ANY,
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Logout"
        )

    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    def test_logout_sesion_ajena(self, mock_session_using):
        """
        Scenario: Authenticated user tries to logout someone else's session.
        Response: 403 Forbidden.
        Audit: SESION_REVOCADA (RECHAZADO).
        """
        user1 = Usuario(id=1, usr_correo="user1@example.com")
        user2 = Usuario(id=2, usr_correo="user2@example.com")
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user2,  # Owned by user2
            estado=EstadoSesion.ACTIVA
        )
        
        mock_session_using.return_value.get.return_value = session

        request = self.factory.post('/api/v1/auth/logout/', {"refresh": "tokenstring"}, format='json')
        force_authenticate(request, user=user1) # Auth as user1
        view = LogoutView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.mock_record_event.assert_any_call(
            usuario=user1,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.SESION_REVOCADA,
            entidad='ses_sesion',
            entidad_id=str(session.id),
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Intento de logout en sesion de otro usuario",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Auth Logout"
        )

    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    def test_safe_jwt_authentication_sesion_revocada(self, mock_session_using):
        """
        Scenario: Submitting an access token for a revoked session fails authentication.
        """
        user = Usuario(id=1, usr_correo="user@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user,
            fecha_expiracion=timezone.now() + timedelta(days=1),
            estado=EstadoSesion.REVOCADA  # Revoked!
        )
        mock_session_using.return_value.get.return_value = session

        # Prepare dummy request
        request = MagicMock()
        request.META = {'HTTP_X_REAL_IP': '127.0.0.1'}

        auth = SafeJWTAuthentication()
        validated_token = {
            'session_id': str(session.id),
            'user_id': user.id
        }

        # Subclass method mock to bypass cryptographic lookup
        with patch('rest_framework_simplejwt.authentication.JWTAuthentication.authenticate') as mock_super_auth:
            mock_super_auth.return_value = (user, validated_token)
            
            with self.assertRaises(InvalidToken) as ctx:
                auth.authenticate(request)
            self.assertIn("La sesión ha expirado, ha sido cerrada o revocada", str(ctx.exception))

            self.mock_record_event.assert_any_call(
                usuario=user,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.ACCESO_CON_SESION_INVALIDA,
                entidad='ses_sesion',
                entidad_id=str(session.id),
                resultado=AuditoriaResultado.RECHAZADO,
                motivo=ANY,
                ip_address='127.0.0.1',
                user_agent=ANY,
                proceso_origen="SafeJWTAuthentication"
            )

    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    def test_safe_jwt_authentication_usuario_inactivo(self, mock_session_using):
        """
        Scenario: Session is active but user is suspended.
        """
        user = Usuario(id=1, usr_correo="user@example.com", estado=EstadoUsuario.SUSPENDIDO, correo_verificado=True)
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user,
            fecha_expiracion=timezone.now() + timedelta(days=1),
            estado=EstadoSesion.ACTIVA
        )
        mock_session_using.return_value.get.return_value = session

        request = MagicMock()
        auth = SafeJWTAuthentication()
        validated_token = {
            'session_id': str(session.id),
            'user_id': user.id
        }

        with patch('rest_framework_simplejwt.authentication.JWTAuthentication.authenticate') as mock_super_auth:
            mock_super_auth.return_value = (user, validated_token)
            
            with self.assertRaises(AuthenticationFailed) as ctx:
                auth.authenticate(request)
            self.assertIn("La cuenta de usuario no está activa", str(ctx.exception))

    def test_ausencia_de_secretos_en_auditoria(self):
        """
        Scenario: Confirm that tokens or passwords are never passed to audit log.
        """
        from apps.audit.services.audit_service import sanitize_dict
        payload = {
            "password": "supersecretpassword",
            "token": "bearer-token-12345",
            "refresh_token": "refresh-token-val",
            "auth_header": "Bearer valid",
            "safe_value": "public"
        }
        sanitized = sanitize_dict(payload)
        self.assertEqual(sanitized["password"], "[REDACTED]")
        self.assertEqual(sanitized["token"], "[REDACTED]")
        self.assertEqual(sanitized["refresh_token"], "[REDACTED]")
        self.assertEqual(sanitized["auth_header"], "[REDACTED]")
        self.assertEqual(sanitized["safe_value"], "public")

    @patch('apps.accounts.models.intento_acceso.IntentoAcceso.save')
    @patch('apps.accounts.models.usuario.Usuario.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_concurrencia_simulada_login_lockout(self, mock_user_using, mock_user_save, mock_attempt_save):
        """
        Scenario: Simulated concurrency race condition.
        Two threads attempt incorrect password login simultaneously when attempts is 4.
        Due to select_for_update, the second thread waits for the first.
        First thread locks user, increments to 5, blocks user, commits.
        Second thread wakes up, gets locked user, checks attempts (now 5), and directly locks out 
        with temporal lock rather than creating inconsistent states.
        """
        user = Usuario(id=1, usr_correo="concurrente@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True, intentos_fallidos=4)
        user.set_password("correctpassword")
        
        # First call to select_for_update returns user with 4 attempts.
        # Second call returns locked_user which now has 5 attempts (after first thread save) and bloqueado_hasta set.
        locked_user_thread_2 = Usuario(id=1, usr_correo="concurrente@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True, intentos_fallidos=5, bloqueado_hasta=timezone.now() + timedelta(minutes=15))
        locked_user_thread_2.set_password("correctpassword")

        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.side_effect = [user, locked_user_thread_2]

        # First request (Thread 1)
        with self.assertRaises(AuthenticationFailed) as ctx1:
            authenticate_and_create_session(email="concurrente@example.com", password="wrongpassword")
        self.assertIn("Credenciales inválidas.", str(ctx1.exception))
        self.assertEqual(user.intentos_fallidos, 5)
        self.assertIsNotNone(user.bloqueado_hasta)

        # Second request (Thread 2) - should immediately hit the lockout check inside transaction!
        with self.assertRaises(AuthenticationFailed) as ctx2:
            authenticate_and_create_session(email="concurrente@example.com", password="wrongpassword")
        self.assertIn("La cuenta se encuentra bloqueada temporalmente.", str(ctx2.exception))

    @patch('apps.accounts.models.sesion.Sesion.save')
    @patch('apps.accounts.models.sesion.Sesion.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_concurrencia_simulada_refresh_rotation(self, mock_user_using, mock_session_using, mock_session_save):
        """
        Scenario: Simulated concurrency race condition during refresh rotation.
        Two threads attempt to refresh using the same refresh token.
        Due to select_for_update, the second thread waits for the first.
        First thread completes and updates token_hash in DB.
        Second thread wakes up, retrieves updated session, detects mismatch,
        revokes the session, and fails.
        """
        user = Usuario(id=1, usr_correo="concurrente@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        session = Sesion(
            id=uuid.uuid4(),
            usuario=user,
            fecha_expiracion=timezone.now() + timedelta(days=1),
            estado=EstadoSesion.ACTIVA
        )

        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_session_using.return_value.select_related.return_value.get.return_value = session

        refresh = RefreshToken()
        refresh['session_id'] = str(session.id)
        refresh['user_id'] = user.id
        refresh_str = str(refresh)
        
        hashed_old_refresh = hash_refresh_token(refresh_str)
        session.token_hash = hashed_old_refresh

        session_updated_thread_2 = Sesion(
            id=session.id,
            usuario=user,
            fecha_expiracion=session.fecha_expiracion,
            estado=EstadoSesion.ACTIVA,
            token_hash=hash_refresh_token("different_new_refresh_token")
        )

        mock_session_using.return_value.select_for_update.return_value.get.side_effect = [
            session,
            session_updated_thread_2
        ]

        access_1, refresh_1 = refresh_user_tokens(
            refresh_token_str=refresh_str,
            ip_address="127.0.0.1",
            user_agent="Mozilla"
        )
        self.assertIsNotNone(access_1)
        self.assertIsNotNone(refresh_1)

        with self.assertRaises(AuthenticationFailed) as ctx:
            refresh_user_tokens(
                refresh_token_str=refresh_str,
                ip_address="127.0.0.1",
                user_agent="Mozilla"
            )
        self.assertIn("La sesión asociada al token no es válida o ha sido revocada.", str(ctx.exception))
        self.assertEqual(session_updated_thread_2.estado, EstadoSesion.REVOCADA)
        self.assertEqual(session_updated_thread_2.motivo_cierre, "Reutilizacion de refresh token detectada")

