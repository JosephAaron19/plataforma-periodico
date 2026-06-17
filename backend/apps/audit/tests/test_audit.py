from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from apps.audit.models.auditoria import Auditoria
from apps.audit.services.audit_service import AuditService, sanitize_dict, truncate_value
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado
from apps.accounts.models.usuario import Usuario

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

    def test_truncate_value(self):
        """
        Verify truncate_value limits string length.
        """
        self.assertEqual(truncate_value("abcdef", 3), "abc")
        self.assertEqual(truncate_value("abc", 5), "abc")
        self.assertIsNone(truncate_value(None, 5))


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
        
        # Should not raise exception, return None
        res = AuditService.record_event(
            proceso_origen="Test",
            modulo=AuditoriaModulo.M02,
            accion=AuditoriaAccion.REGISTRO_USUARIO,
            entidad='usr_usuario',
            resultado=AuditoriaResultado.EXITOSO,
            throw_on_error=False
        )
        self.assertIsNone(res)

        # Should raise exception when throw_on_error is True
        with self.assertRaises(Exception):
            AuditService.record_event(
                proceso_origen="Test",
                modulo=AuditoriaModulo.M02,
                accion=AuditoriaAccion.REGISTRO_USUARIO,
                entidad='usr_usuario',
                resultado=AuditoriaResultado.EXITOSO,
                throw_on_error=True
            )
