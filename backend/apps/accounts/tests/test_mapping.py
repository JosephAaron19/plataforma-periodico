from django.test import SimpleTestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock, PropertyMock
from apps.accounts.models import Usuario, Perfil, Sesion, RecuperacionCuenta, IntentoAcceso, VerificacionCorreo
from apps.accounts.constants import EstadoUsuario
from apps.accounts.services.password_service import hash_password, check_password, is_password_usable
from apps.accounts.selectors.usuario_selectors import (
    get_user_by_email, get_user_by_id, get_user_profile,
    get_active_sessions, get_active_recoveries
)

class AccountsMappingSafeTest(SimpleTestCase):
    # This inherits from SimpleTestCase to ensure no database connection is initiated during tests.

    def test_models_are_unmanaged(self):
        """
        Verify that managed = False is declared for all accounts models.
        """
        self.assertFalse(Usuario._meta.managed)
        self.assertFalse(Perfil._meta.managed)
        self.assertFalse(Sesion._meta.managed)
        self.assertFalse(RecuperacionCuenta._meta.managed)
        self.assertFalse(IntentoAcceso._meta.managed)
        self.assertFalse(VerificacionCorreo._meta.managed)

    def test_meta_db_table_mapping(self):
        """
        Verify that the models point exactly to the correct tables in the 'pdg' schema.
        """
        self.assertEqual(Usuario._meta.db_table, 'pdg"."usr_usuario')
        self.assertEqual(Perfil._meta.db_table, 'pdg"."prf_perfil')
        self.assertEqual(Sesion._meta.db_table, 'pdg"."ses_sesion')
        self.assertEqual(RecuperacionCuenta._meta.db_table, 'pdg"."rec_recuperacion_cuenta')
        self.assertEqual(IntentoAcceso._meta.db_table, 'pdg"."ina_intento_acceso')
        self.assertEqual(VerificacionCorreo._meta.db_table, 'pdg"."ver_verificacion_correo')

    def test_db_column_mappings(self):
        """
        Verify exact db_column names mapping for primary keys and key columns.
        """
        # Usuario
        self.assertEqual(Usuario._meta.get_field('id').db_column, 'usr_id')
        self.assertEqual(Usuario._meta.get_field('usr_correo').db_column, 'usr_correo')
        self.assertEqual(Usuario._meta.get_field('password').db_column, 'usr_clave_hash')
        self.assertEqual(Usuario._meta.get_field('last_login').db_column, 'usr_ultimo_acceso')
        self.assertEqual(Usuario._meta.get_field('nombres').db_column, 'usr_nombres')
        
        # Perfil
        self.assertEqual(Perfil._meta.get_field('id').db_column, 'prf_id')
        self.assertEqual(Perfil._meta.get_field('usuario').db_column, 'usr_id')
        
        # Sesion
        self.assertEqual(Sesion._meta.get_field('id').db_column, 'ses_id')
        self.assertEqual(Sesion._meta.get_field('usuario').db_column, 'usr_id')
        
        # RecuperacionCuenta
        self.assertEqual(RecuperacionCuenta._meta.get_field('id').db_column, 'rec_id')
        self.assertEqual(RecuperacionCuenta._meta.get_field('usuario').db_column, 'usr_id')
        
        # IntentoAcceso
        self.assertEqual(IntentoAcceso._meta.get_field('id').db_column, 'ina_id')
        self.assertEqual(IntentoAcceso._meta.get_field('usuario').db_column, 'usr_id')
        
        # VerificacionCorreo
        self.assertEqual(VerificacionCorreo._meta.get_field('id').db_column, 'ver_id')
        self.assertEqual(VerificacionCorreo._meta.get_field('usuario').db_column, 'usr_id')

    def test_model_primary_keys(self):
        """
        Verify that primary keys are correctly defined on the model classes.
        """
        self.assertTrue(Usuario._meta.get_field('id').primary_key)
        self.assertTrue(Perfil._meta.get_field('id').primary_key)
        self.assertTrue(Sesion._meta.get_field('id').primary_key)
        self.assertTrue(RecuperacionCuenta._meta.get_field('id').primary_key)
        self.assertTrue(IntentoAcceso._meta.get_field('id').primary_key)
        self.assertTrue(VerificacionCorreo._meta.get_field('id').primary_key)

    def test_model_relationships_declared(self):
        """
        Verify relationship types and related names.
        """
        # Perfil - OneToOne relation
        perfil_field = Usuario._meta.get_field('perfil')
        self.assertTrue(perfil_field.one_to_one)
        self.assertEqual(perfil_field.related_model, Perfil)
        
        # Sesion - ForeignKey relation
        sesion_rel = Usuario._meta.get_field('sesiones')
        self.assertTrue(sesion_rel.one_to_many)
        self.assertEqual(sesion_rel.related_model, Sesion)

        # Recuperaciones - ForeignKey relation
        rec_rel = Usuario._meta.get_field('recuperaciones')
        self.assertTrue(rec_rel.one_to_many)
        self.assertEqual(rec_rel.related_model, RecuperacionCuenta)

        # Intentos - ForeignKey relation
        int_rel = Usuario._meta.get_field('intentos_acceso')
        self.assertTrue(int_rel.one_to_many)
        self.assertEqual(int_rel.related_model, IntentoAcceso)

        # Verificaciones - ForeignKey relation
        ver_rel = Usuario._meta.get_field('verificaciones_correo')
        self.assertTrue(ver_rel.one_to_many)
        self.assertEqual(ver_rel.related_model, VerificacionCorreo)

    def test_email_normalization(self):
        """
        Verify email normalizer lowers and trims whitespaces.
        """
        normalized = Usuario.objects.normalize_email("   USER_Test@Domain.COM   ")
        self.assertEqual(normalized, "user_test@domain.com")
        self.assertEqual(Usuario.objects.normalize_email(""), "")
        self.assertEqual(Usuario.objects.normalize_email(None), "")

    def test_password_hash_not_exposed(self):
        """
        Verify that user string/repr formats never leak password hashes.
        """
        usr = Usuario(usr_correo="safe@domain.com", password="pbkdf2_sha256$260000$somehashedpasswordvalue")
        self.assertNotIn("pbkdf2", str(usr))
        self.assertNotIn("hashedpassword", str(usr))
        self.assertNotIn("pbkdf2", repr(usr))
        self.assertNotIn("hashedpassword", repr(usr))

    def test_user_properties_and_state(self):
        """
        Verify is_active, is_staff, is_superuser properties and permission mock methods.
        """
        # Activo, not deleted, no locks
        u1 = Usuario(estado=EstadoUsuario.ACTIVO, eliminado=False)
        self.assertTrue(u1.is_active)
        
        # Deleted
        u2 = Usuario(estado=EstadoUsuario.ACTIVO, eliminado=True)
        self.assertFalse(u2.is_active)
        
        # Blocked
        u3 = Usuario(estado=EstadoUsuario.BLOQUEADO, eliminado=False)
        self.assertFalse(u3.is_active)
        
        # Temporally locked
        future_time = timezone.now() + timezone.timedelta(hours=1)
        u4 = Usuario(estado=EstadoUsuario.ACTIVO, eliminado=False, bloqueado_hasta=future_time)
        self.assertFalse(u4.is_active)
        
        # Expired lock
        past_time = timezone.now() - timezone.timedelta(hours=1)
        u5 = Usuario(estado=EstadoUsuario.ACTIVO, eliminado=False, bloqueado_hasta=past_time)
        self.assertTrue(u5.is_active)

        # Staff / Superuser logic checks (temporary runtime behavior)
        self.assertFalse(u1.is_staff)
        self.assertFalse(u1.is_superuser)
        self.assertFalse(u1.has_perm("some_permission"))
        self.assertFalse(u1.has_module_perms("some_app"))

    def test_password_service(self):
        """
        Verify password service operations (hashing, check, is_usable) using non-persisted instances.
        """
        raw_pw = "MySecretPass123"
        hashed = hash_password(raw_pw)
        self.assertTrue(is_password_usable(hashed))
        self.assertTrue(check_password(raw_pw, hashed))
        self.assertFalse(check_password("WrongPassword", hashed))
        self.assertFalse(is_password_usable(""))
        self.assertFalse(check_password("", ""))

    @patch('apps.accounts.models.usuario.Usuario.objects.get')
    def test_selectors_by_email_and_id(self, mock_get):
        """
        Verify selector functions search and filter using mocked database queries.
        """
        mock_user = MagicMock(spec=Usuario)
        mock_get.return_value = mock_user
        
        # By email
        user_res = get_user_by_email("test@domain.com")
        self.assertEqual(user_res, mock_user)
        mock_get.assert_called_with(usr_correo="test@domain.com")
        
        # By ID
        mock_get.reset_mock()
        user_res_id = get_user_by_id(123)
        self.assertEqual(user_res_id, mock_user)
        mock_get.assert_called_with(pk=123)

    def test_selectors_profile_and_active_relations(self):
        """
        Verify selector functions traverse relationships with mock users.
        """
        user = Usuario()
        
        # Profile exists
        mock_profile = MagicMock(spec=Perfil)
        with patch.object(Usuario, 'perfil', new_callable=PropertyMock) as mock_perfil_prop:
            mock_perfil_prop.return_value = mock_profile
            self.assertEqual(get_user_profile(user), mock_profile)
        
        # Profile does not exist
        with patch.object(Usuario, 'perfil', new_callable=PropertyMock) as mock_perfil_prop:
            mock_perfil_prop.side_effect = Perfil.DoesNotExist
            self.assertIsNone(get_user_profile(user))

    @patch('apps.accounts.models.sesion.Sesion.objects.filter')
    def test_selectors_active_sessions(self, mock_filter):
        mock_user = MagicMock(spec=Usuario)
        get_active_sessions(mock_user)
        mock_filter.assert_called_once()
        
    @patch('apps.accounts.models.recuperacion.RecuperacionCuenta.objects.filter')
    def test_selectors_active_recoveries(self, mock_filter):
        mock_user = MagicMock(spec=Usuario)
        get_active_recoveries(mock_user)
        mock_filter.assert_called_once()
