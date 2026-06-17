from django.test import SimpleTestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import ValidationError
from apps.accounts.models.usuario import Usuario
from apps.accounts.models.verificacion_correo import VerificacionCorreo
from apps.accounts.constants import EstadoUsuario, EstadoVerificacion
from apps.accounts.serializers.register import UserRegisterSerializer
from apps.accounts.serializers.verify import EmailVerifySerializer
from apps.accounts.services.register_service import register_user
from apps.accounts.services.verification_service import verify_email
import uuid

class DummyAtomic:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

@patch('django.db.transaction.atomic', DummyAtomic)
class RegistrationFlowTest(SimpleTestCase):
    
    @patch('apps.accounts.models.usuario.Usuario.objects.filter')
    def test_register_serializer_validation(self, mock_filter):
        """
        Verify that registration serializer validates input fields correctly.
        """
        mock_filter.return_value.exists.return_value = False
        
        # Weak password
        data_weak = {
            "email": "test@example.com",
            "password": "short",
            "nombres": "John"
        }
        serializer = UserRegisterSerializer(data=data_weak)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        
        # Missing names
        data_no_name = {
            "email": "test@example.com",
            "password": "validpassword123",
            "nombres": ""
        }
        serializer = UserRegisterSerializer(data=data_no_name)
        self.assertFalse(serializer.is_valid())
        
        # Valid data
        data_valid = {
            "email": "test@example.com",
            "password": "validpassword123",
            "nombres": "John",
            "apellidos": "Doe"
        }
        serializer = UserRegisterSerializer(data=data_valid)
        self.assertTrue(serializer.is_valid())

    @patch('apps.accounts.services.register_service.send_verification_email')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.usuario.Usuario.save')
    @patch('apps.accounts.models.usuario.Usuario.objects.filter')
    def test_register_user_service_success(self, mock_user_filter, mock_user_save, mock_verification_save, mock_send_email):
        """
        Verify register_user service inserts user/token and triggers email.
        """
        mock_user_filter.return_value.exists.return_value = False
        
        user = register_user(
            email="newuser@example.com",
            password="securepassword123",
            nombres="Jane",
            apellidos="Doe",
            ip_address="127.0.0.1"
        )
        
        self.assertEqual(user.usr_correo, "newuser@example.com")
        self.assertEqual(user.estado, EstadoUsuario.PENDIENTE)
        self.assertFalse(user.correo_verificado)
        
        # Check database saves and email trigger were called
        mock_user_save.assert_called_once()
        mock_verification_save.assert_called_once()
        mock_send_email.assert_called_once()

    @patch('apps.accounts.models.usuario.Usuario.objects.filter')
    def test_register_user_duplicate_email(self, mock_user_filter):
        """
        Verify register_user service raises error on duplicate emails.
        """
        mock_user_filter.return_value.exists.return_value = True
        
        with self.assertRaises(ValidationError) as ctx:
            register_user(
                email="duplicate@example.com",
                password="securepassword123",
                nombres="Jane"
            )
        self.assertIn("El correo electrónico ya se encuentra registrado", str(ctx.exception))


@patch('django.db.transaction.atomic', DummyAtomic)
class VerificationFlowTest(SimpleTestCase):

    def test_verify_serializer_validation(self):
        """
        Verify verification serializer requires a token.
        """
        serializer = EmailVerifySerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)
        
        serializer_valid = EmailVerifySerializer(data={"token": "sometoken"})
        self.assertTrue(serializer_valid.is_valid())

    @patch('apps.accounts.models.usuario.Usuario.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.select_related')
    def test_verify_email_success(self, mock_select_related, mock_verification_save, mock_user_save):
        """
        Verify verify_email service updates token status and activates user.
        """
        mock_user = Usuario(
            usr_correo="verify@example.com",
            estado=EstadoUsuario.PENDIENTE,
            correo_verificado=False
        )
        mock_verification = VerificacionCorreo(
            id=uuid.uuid4(),
            usuario=mock_user,
            fecha_expiracion=timezone.now() + timedelta(hours=24),
            estado=EstadoVerificacion.PENDIENTE,
            intentos=0
        )
        
        mock_select_related.return_value.get.return_value = mock_verification
        
        result_ver = verify_email(plain_token="testtoken123", ip_address="127.0.0.1")
        
        self.assertEqual(result_ver.estado, EstadoVerificacion.VERIFICADA)
        self.assertIsNotNone(result_ver.fecha_verificacion)
        
        # User should be active now
        self.assertEqual(mock_user.estado, EstadoUsuario.ACTIVO)
        self.assertTrue(mock_user.correo_verificado)
        self.assertIsNotNone(mock_user.fecha_verificacion)
        
        mock_verification_save.assert_called_once()
        mock_user_save.assert_called_once()

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.select_related')
    def test_verify_email_expired(self, mock_select_related, mock_verification_save):
        """
        Verify verify_email service rejects and invalidates expired tokens.
        """
        mock_user = Usuario(usr_correo="expired@example.com")
        mock_verification = VerificacionCorreo(
            id=uuid.uuid4(),
            usuario=mock_user,
            fecha_expiracion=timezone.now() - timedelta(hours=1), # Expired 1 hour ago
            estado=EstadoVerificacion.PENDIENTE,
            intentos=0
        )
        mock_select_related.return_value.get.return_value = mock_verification
        
        with self.assertRaises(ValidationError) as ctx:
            verify_email(plain_token="testtoken123")
            
        self.assertIn("El enlace de verificación ha expirado", str(ctx.exception))
        self.assertEqual(mock_verification.estado, EstadoVerificacion.VENCIDA)
        mock_verification_save.assert_called_once()

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.select_related')
    def test_verify_email_already_used(self, mock_select_related, mock_verification_save):
        """
        Verify verify_email service rejects already verified tokens.
        """
        mock_user = Usuario(usr_correo="already@example.com")
        mock_verification = VerificacionCorreo(
            id=uuid.uuid4(),
            usuario=mock_user,
            fecha_expiracion=timezone.now() + timedelta(hours=24),
            estado=EstadoVerificacion.VERIFICADA,
            fecha_verificacion=timezone.now(),
            intentos=1
        )
        mock_select_related.return_value.get.return_value = mock_verification
        
        with self.assertRaises(ValidationError) as ctx:
            verify_email(plain_token="testtoken123")
            
        self.assertIn("El correo ya ha sido verificado anteriormente", str(ctx.exception))
        self.assertEqual(mock_verification.intentos, 2)
        mock_verification_save.assert_called_once()

    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.save')
    @patch('apps.accounts.models.verificacion_correo.VerificacionCorreo.objects.select_related')
    def test_verify_email_brute_force_prevention(self, mock_select_related, mock_verification_save):
        """
        Verify verify_email invalidates token after 5 failed attempts.
        """
        mock_user = Usuario(usr_correo="bruteforce@example.com")
        mock_verification = VerificacionCorreo(
            id=uuid.uuid4(),
            usuario=mock_user,
            fecha_expiracion=timezone.now() + timedelta(hours=24),
            estado=EstadoVerificacion.PENDIENTE,
            intentos=5 # Next attempt will be the 6th
        )
        mock_select_related.return_value.get.return_value = mock_verification
        
        with self.assertRaises(ValidationError) as ctx:
            verify_email(plain_token="testtoken123")
            
        self.assertIn("Token bloqueado por exceso de intentos fallidos", str(ctx.exception))
        self.assertEqual(mock_verification.estado, EstadoVerificacion.INVALIDADA)
        self.assertEqual(mock_verification.motivo_invalidacion, "Exceso de intentos de verificación")
        mock_verification_save.assert_called_once()
