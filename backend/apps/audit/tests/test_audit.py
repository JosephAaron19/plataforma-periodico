from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from apps.audit.models.auditoria import Auditoria
from apps.audit.services.audit_service import AuditService, sanitize_dict, truncate_value
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
from apps.audit.utils import get_client_ip
from apps.accounts.models.usuario import Usuario

class DummyAtomic:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class AuditoriaModelTest(SimpleTestCase):
    def test_model_meta(self):
        """
        Verify that Auditoria model is unmanaged and points to correct schema table.
        """
        self.assertFalse(Auditoria._meta.managed)
        self.assertEqual(Auditoria._meta.db_table, 'pdg"."aud_auditoria')

    def test_model_fields_db_column(self):
        """
        Verify that the fields are mapped to correct database columns.
        """
        self.assertEqual(Auditoria._meta.get_field('usuario').db_column, 'usr_id')
        self.assertEqual(Auditoria._meta.get_field('emp_id').db_column, 'emp_id')
        self.assertEqual(Auditoria._meta.get_field('modulo').db_column, 'aud_modulo')
        self.assertEqual(Auditoria._meta.get_field('accion').db_column, 'aud_accion')
        self.assertEqual(Auditoria._meta.get_field('entidad').db_column, 'aud_entidad')
        self.assertEqual(Auditoria._meta.get_field('entidad_id').db_column, 'aud_entidad_id')
        self.assertEqual(Auditoria._meta.get_field('valores_anteriores').db_column, 'aud_valores_anteriores')
        self.assertEqual(Auditoria._meta.get_field('valores_nuevos').db_column, 'aud_valores_nuevos')
        self.assertEqual(Auditoria._meta.get_field('resultado').db_column, 'aud_resultado')
        self.assertEqual(Auditoria._meta.get_field('motivo').db_column, 'aud_motivo')
        self.assertEqual(Auditoria._meta.get_field('direccion_ip').db_column, 'aud_direccion_ip')
        self.assertEqual(Auditoria._meta.get_field('agente_usuario').db_column, 'aud_agente_usuario')
        self.assertEqual(Auditoria._meta.get_field('proceso_origen').db_column, 'aud_proceso_origen')
        self.assertEqual(Auditoria._meta.get_field('fecha').db_column, 'aud_fecha')

    def test_foreign_key_on_delete_behavior(self):
        """
        Verify that foreign key delete rule maps to DO_NOTHING.
        """
        from django.db.models import DO_NOTHING
        field = Auditoria._meta.get_field('usuario')
        self.assertEqual(field.remote_field.on_delete, DO_NOTHING)


class AuditServiceSanitizationTest(SimpleTestCase):
    def test_sanitize_dict_redaction(self):
        """
        Verify that sanitize_dict redacts all specified sensitive keys recursively.
        """
        dirty_data = {
            "password": "mysecretpassword",
            "password_confirmation": "mysecretpassword",
            "token": "secret_token_123",
            "access": "access_token_abc",
            "refresh": "refresh_token_xyz",
            "usr_clave_hash": "somehash",
            "ver_token_hash": "anotherhash",
            "authorization": "Bearer token",
            "cookie": "session_id=123",
            "nested": {
                "password": "nestedpassword",
                "normal_field": "safe_data"
            },
            "normal_field": "safe_data",
            "list_field": [
                {"token": "listtoken"},
                {"safe": "data"}
            ]
        }
        
        clean_data = sanitize_dict(dirty_data)
        
        self.assertEqual(clean_data["password"], "[REDACTED]")
        self.assertEqual(clean_data["password_confirmation"], "[REDACTED]")
        self.assertEqual(clean_data["token"], "[REDACTED]")
        self.assertEqual(clean_data["access"], "[REDACTED]")
        self.assertEqual(clean_data["refresh"], "[REDACTED]")
        self.assertEqual(clean_data["usr_clave_hash"], "[REDACTED]")
        self.assertEqual(clean_data["ver_token_hash"], "[REDACTED]")
        self.assertEqual(clean_data["authorization"], "[REDACTED]")
        self.assertEqual(clean_data["cookie"], "[REDACTED]")
        self.assertEqual(clean_data["nested"]["password"], "[REDACTED]")
        self.assertEqual(clean_data["nested"]["normal_field"], "safe_data")
        self.assertEqual(clean_data["normal_field"], "safe_data")
        self.assertEqual(clean_data["list_field"][0]["token"], "[REDACTED]")
        self.assertEqual(clean_data["list_field"][1]["safe"], "data")

    def test_sanitize_dict_no_mutation(self):
        """
        Verify that sanitize_dict does not mutate original objects.
        """
        original = {
            "Password": "mysecretpassword",
            "nested": {
                "token": "secret_token"
            }
        }
        sanitized = sanitize_dict(original)
        
        self.assertEqual(original["Password"], "mysecretpassword")
        self.assertEqual(original["nested"]["token"], "secret_token")
        self.assertEqual(sanitized["Password"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["token"], "[REDACTED]")

    def test_sanitize_dict_case_insensitive_and_partial(self):
        """
        Verify that sanitization handles mixed case and partial keywords.
        """
        original = {
            "my_password_value": "secret",
            "Verification_Token": "token123",
            "AUTH_header": "Bearer abc"
        }
        sanitized = sanitize_dict(original)
        self.assertEqual(sanitized["my_password_value"], "[REDACTED]")
        self.assertEqual(sanitized["Verification_Token"], "[REDACTED]")
        self.assertEqual(sanitized["AUTH_header"], "[REDACTED]")

    def test_truncate_value(self):
        """
        Verify truncate_value limits string length.
        """
        self.assertEqual(truncate_value("abcdef", 3), "abc")
        self.assertEqual(truncate_value("abc", 5), "abc")
        self.assertIsNone(truncate_value(None, 5))


class AuditIPValidationTest(SimpleTestCase):
    def test_get_client_ip_real_ip(self):
        """
        Verify that X-Real-IP is preferred.
        """
        request = MagicMock()
        request.META = {
            'HTTP_X_REAL_IP': '192.168.1.50',
            'REMOTE_ADDR': '127.0.0.1'
        }
        self.assertEqual(get_client_ip(request), '192.168.1.50')

    def test_get_client_ip_fallback_remote_addr(self):
        """
        Verify fallback to REMOTE_ADDR.
        """
        request = MagicMock()
        request.META = {
            'REMOTE_ADDR': '127.0.0.1'
        }
        self.assertEqual(get_client_ip(request), '127.0.0.1')

    def test_get_client_ip_invalid_format(self):
        """
        Verify that invalid IP strings are rejected and return None.
        """
        request = MagicMock()
        request.META = {
            'HTTP_X_REAL_IP': 'invalid-ip-string',
            'REMOTE_ADDR': '127.0.0.1'
        }
        self.assertIsNone(get_client_ip(request))

    def test_get_client_ip_no_forwarded_for_trust(self):
        """
        Verify that X-Forwarded-For is ignored in favor of REMOTE_ADDR if Real-IP is missing.
        """
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '8.8.8.8, 9.9.9.9',
            'REMOTE_ADDR': '127.0.0.1'
        }
        self.assertEqual(get_client_ip(request), '127.0.0.1')


@patch('django.db.transaction.atomic', DummyAtomic)
class AuditServiceTest(SimpleTestCase):
    @patch('apps.audit.models.auditoria.Auditoria.save')
    def test_record_event_success(self, mock_save):
        """
        Verify recording event works correctly and calls save.
        """
        mock_user = MagicMock(spec=Usuario)
        mock_user._meta = MagicMock()
        mock_user._meta.app_label = 'accounts'
        mock_user._state = MagicMock()
        mock_state_db = MagicMock()
        mock_state_db.db = 'periodico_db'
        mock_user._state = mock_state_db
        
        event = AuditService.record_event(
            usuario=mock_user,
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REGISTRO_USUARIO,
            entidad='usr_usuario',
            resultado=AuditoriaResultado.EXITOSO,
            ip_address="127.0.0.1",
            user_agent="Mozilla",
            proceso_origen="Test"
        )
        self.assertIsNotNone(event)
        mock_save.assert_called_once()

    def test_record_event_validation_fail_origin(self):
        """
        Verify validation fails if both usuario and proceso_origen are missing.
        """
        with self.assertRaises(ValidationError):
            AuditService.record_event(
                usuario=None,
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REGISTRO_USUARIO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.EXITOSO,
                proceso_origen=None,
                throw_on_error=True
            )

    def test_record_event_validation_fail_modulo(self):
        """
        Verify validation fails if modulo is not allowed by CHECK constraint.
        """
        with self.assertRaises(ValidationError):
            AuditService.record_event(
                proceso_origen="Test",
                modulo="INVALID_MODULO",
                accion=AuditoriaAccion.REGISTRO_USUARIO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.EXITOSO,
                throw_on_error=True
            )

    def test_record_event_validation_fail_resultado(self):
        """
        Verify validation fails if resultado is not allowed.
        """
        with self.assertRaises(ValidationError):
            AuditService.record_event(
                proceso_origen="Test",
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REGISTRO_USUARIO,
                entidad='usr_usuario',
                resultado="INVALID_RESULT",
                throw_on_error=True
            )

    @patch('apps.audit.models.auditoria.Auditoria.save')
    def test_record_event_graceful_error_handling(self, mock_save):
        """
        Verify that save errors are caught and return None if throw_on_error is False.
        """
        mock_save.side_effect = Exception("Database is down")
        
        res = AuditService.record_event(
            proceso_origen="Test",
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REGISTRO_USUARIO,
            entidad='usr_usuario',
            resultado=AuditoriaResultado.EXITOSO,
            throw_on_error=False
        )
        self.assertIsNone(res)

        with self.assertRaises(Exception):
            AuditService.record_event(
                proceso_origen="Test",
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REGISTRO_USUARIO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.EXITOSO,
                throw_on_error=True
            )

    @patch('apps.audit.models.auditoria.Auditoria.save')
    def test_record_event_savepoint_preserves_outer_transaction(self, mock_save):
        """
        Verify that saving audit triggers an atomic block with savepoint=True.
        """
        from django.db import IntegrityError
        mock_save.side_effect = IntegrityError("Database constraint error")
        
        with patch('django.db.transaction.atomic') as mock_atomic:
            res = AuditService.record_event(
                proceso_origen="Test",
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REGISTRO_USUARIO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.EXITOSO,
                throw_on_error=False
            )
            self.assertIsNone(res)
            mock_atomic.assert_called_with(using='periodico_db', savepoint=True)
