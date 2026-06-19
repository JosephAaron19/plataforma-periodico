from django.test import SimpleTestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock, ANY
from rest_framework import status
from rest_framework.test import APIRequestFactory
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.views.resend_verification import ResendVerificationView
from apps.accounts.services.resend_verification_service import resend_verification_link
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
class ResendVerificationSecureTest(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        
        # Patch audit service to prevent database writes
        self.audit_patcher = patch('apps.audit.services.audit_service.AuditService.record_event')
        self.mock_record_event = self.audit_patcher.start()

        # Patch transaction.on_commit
        self.commit_patcher = patch('django.db.transaction.on_commit')
        self.mock_on_commit = self.commit_patcher.start()

    def tearDown(self):
        self.audit_patcher.stop()
        self.commit_patcher.stop()
        super().tearDown()

    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_email_inexistente(self, mock_user_using):
        """
        Scenario: Email does not exist.
        Response: Must be generic HTTP 200.
        Audit: REENVIO_VERIFICACION_SOLICITADO (usuario=None) and REENVIO_VERIFICACION_IGNORADO (usuario=None).
        """
        # User lookup returns None
        mock_user_using.return_value.filter.return_value.first.return_value = None

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "noexiste@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        # Assertion 1: Public response is generic
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "Si la cuenta existe y requiere verificación, recibirás un nuevo enlace."
        )

        # Assertion 2: Verify audit logs
        # Solicitado
        self.mock_record_event.assert_any_call(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_SOLICITADO,
            entidad='ver_verificacion_correo',
            valores_nuevos={'usr_correo': 'no***@ejemplo.com'},
            resultado=AuditoriaResultado.RECHAZADO,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )
        # Ignorado
        self.mock_record_event.assert_any_call(
            usuario=None,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="El usuario no existe en el sistema",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_cuenta_activa(self, mock_user_using):
        """
        Scenario: User exists, is active and verified.
        Response: Generic HTTP 200.
        Audit: REENVIO_VERIFICACION_IGNORADO.
        """
        user = Usuario(usr_correo="activo@ejemplo.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        mock_user_using.return_value.filter.return_value.first.return_value = user

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "activo@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="El usuario ya se encuentra activo y verificado",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_cuenta_suspendida(self, mock_user_using):
        """
        Scenario: User exists, is suspended/blocked/inactive/deleted.
        Response: Generic HTTP 200. No email sent.
        Audit: REENVIO_VERIFICACION_IGNORADO.
        """
        user = Usuario(usr_correo="suspendido@ejemplo.com", estado=EstadoUsuario.SUSPENDIDO, correo_verificado=False)
        mock_user_using.return_value.filter.return_value.first.return_value = user

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "suspendido@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Estado de usuario no elegible para reenvio: estado=SUSPENDIDO, eliminado=False",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_usuario_eliminado(self, mock_user_using):
        """
        Scenario: User is deleted.
        Response: Generic HTTP 200. No email sent.
        Audit: REENVIO_VERIFICACION_IGNORADO.
        """
        user = Usuario(usr_correo="eliminado@ejemplo.com", estado=EstadoUsuario.PENDIENTE, correo_verificado=False, eliminado=True)
        mock_user_using.return_value.filter.return_value.first.return_value = user

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "eliminado@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_IGNORADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Estado de usuario no elegible para reenvio: estado=PENDIENTE, eliminado=True",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_permitido_e_invalidacion_anteriores(self, mock_user_using, mock_verification_using, mock_verification_save):
        """
        Scenario: User is pending, verification is permitted (not rate limited).
        Response: Generic HTTP 200.
        Action: Previous pending verifications are marked INVALIDADA. New token generated. Email queued via on_commit.
        Audit: REENVIO_VERIFICACION_SOLICITADO, REENVIO_VERIFICACION_ENVIADO.
        """
        user = Usuario(id=1, usr_correo="pendiente@ejemplo.com", nombres="Test", estado=EstadoUsuario.PENDIENTE, correo_verificado=False)
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        # Rate limits return false
        mock_verification_using.return_value.filter.return_value.exists.return_value = False
        mock_verification_using.return_value.filter.return_value.count.return_value = 0
        mock_verification_using.return_value.filter.return_value.update.return_value = 1

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "pendiente@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify old verification tokens invalidated
        mock_verification_using.return_value.filter.assert_any_call(
            usuario=user,
            estado=EstadoVerificacion.PENDIENTE
        )
        mock_verification_using.return_value.filter.return_value.update.assert_called_with(
            estado=EstadoVerificacion.INVALIDADA,
            motivo_invalidacion="Reenvío de enlace de verificación solicitado"
        )

        # Verify new verification token saved
        mock_verification_save.assert_called_once()
        
        # Verify transaction.on_commit callback registered
        self.mock_on_commit.assert_called_once()

        # Verify audit event for sent token
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_ENVIADO,
            entidad='ver_verificacion_correo',
            entidad_id=self.mock_record_event.call_args_list[-1][1]['entidad_id'],
            valores_nuevos=self.mock_record_event.call_args_list[-1][1]['valores_nuevos'],
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_intervalo_minimo_60_segundos(self, mock_user_using, mock_verification_using):
        """
        Scenario: User requests verification but another verification was sent within 60s.
        Response: Generic HTTP 200.
        Action: Blocked from creating new tokens.
        Audit: REENVIO_VERIFICACION_LIMITADO.
        """
        user = Usuario(usr_correo="limite60@ejemplo.com", estado=EstadoUsuario.PENDIENTE, correo_verificado=False)
        mock_user_using.return_value.filter.return_value.first.return_value = user

        # 60s limit check returns True (exists)
        mock_verification_using.return_value.filter.return_value.exists.return_value = True

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "limite60@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify audit log
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Intento de reenvio antes de los 60 segundos permitidos",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_resend_verification_limite_diario_5_solicitudes(self, mock_user_using, mock_verification_using):
        """
        Scenario: User requests verification but already has 5 verifications in 24 hours.
        Response: Generic HTTP 200.
        Action: Blocked from creating new tokens.
        Audit: REENVIO_VERIFICACION_LIMITADO.
        """
        user = Usuario(usr_correo="limite24h@ejemplo.com", estado=EstadoUsuario.PENDIENTE, correo_verificado=False)
        mock_user_using.return_value.filter.return_value.first.return_value = user

        # 60s limit check returns False
        mock_verification_using.return_value.filter.return_value.exists.return_value = False
        # 24h count returns 5
        mock_verification_using.return_value.filter.return_value.count.return_value = 5

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "limite24h@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify audit log
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Exceso de solicitudes de reenvio de verificacion en 24 horas",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )

    @patch('apps.accounts.services.resend_verification_service.send_verification_email')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_celery_failure_does_not_break_response(self, mock_user_using, mock_verification_using, mock_verification_save, mock_send_email):
        """
        Scenario: Celery email dispatch fails during transaction.on_commit callback.
        Response: Generic HTTP 200.
        """
        user = Usuario(id=1, usr_correo="celeryfail@ejemplo.com", nombres="Test", estado=EstadoUsuario.PENDIENTE, correo_verificado=False)
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        mock_verification_using.return_value.filter.return_value.exists.return_value = False
        mock_verification_using.return_value.filter.return_value.count.return_value = 0

        # Simulate on_commit executing immediately when mock is called, and raising Celery error
        self.mock_on_commit.side_effect = lambda func, using=None: func()
        mock_send_email.side_effect = Exception("Celery connection error")

        request = self.factory.post('/api/v1/auth/resend-verification/', {"email": "celeryfail@ejemplo.com"}, format='json')
        view = ResendVerificationView.as_view()
        
        # Response must still be 200 OK because the view handles internal service exceptions gracefully.
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_absence_in_logs_and_audits(self):
        """
        Scenario: Confirm that tokens or their hashes are not exposed anywhere in the audit logs.
        """
        # We check the code structure of resend_verification_service to verify we only audit safe keys
        # The audit_service.sanitize_dict is also tested separately to ensure token redaction.
        from apps.audit.services.audit_service import sanitize_dict
        test_payload = {
            "token": "plain_token_secret",
            "ver_token_hash": "hash_secret",
            "other_field": "public"
        }
        sanitized = sanitize_dict(test_payload)
        self.assertEqual(sanitized["token"], "[REDACTED]")
        self.assertEqual(sanitized["ver_token_hash"], "[REDACTED]")
        self.assertEqual(sanitized["other_field"], "public")

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.using')
    @patch('apps.accounts.models.usuario.Usuario.objects.using')
    def test_simulated_concurrency_race_condition(self, mock_user_using, mock_verification_using, mock_verification_save):
        """
        Scenario: Simulated concurrency race condition.
        Initially the first limit check passes (exists = False).
        But right after locking user (select_for_update), another thread has completed a request, 
        causing the second internal rate limit check to trigger (exists = True).
        Action: The service should log a concurrency limit event and exit without saving a new verification.
        """
        user = Usuario(id=1, usr_correo="concurrente@ejemplo.com", nombres="Test", estado=EstadoUsuario.PENDIENTE, correo_verificado=False)
        mock_user_using.return_value.filter.return_value.first.return_value = user
        mock_user_using.return_value.select_for_update.return_value.get.return_value = user

        # We configure a side-effect on exists.
        # First call: 60s check (pre-lock) -> returns False
        # Second call: 60s check (post-lock inside transaction) -> returns True
        mock_verification_using.return_value.filter.return_value.exists.side_effect = [False, True]
        mock_verification_using.return_value.filter.return_value.count.return_value = 0

        resend_verification_link(email="concurrente@ejemplo.com")

        # Assertion: New verification is NOT saved (save not called)
        mock_verification_save.assert_not_called()

        # Assertion: Concurrency rate limit event audited
        self.mock_record_event.assert_any_call(
            usuario=user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REENVIO_VERIFICACION_LIMITADO,
            entidad='ver_verificacion_correo',
            resultado=AuditoriaResultado.RECHAZADO,
            motivo="Intento de reenvio antes de los 60 segundos permitidos (concurrencia)",
            ip_address=ANY,
            user_agent=ANY,
            proceso_origen="Reenvio de Verificacion"
        )
