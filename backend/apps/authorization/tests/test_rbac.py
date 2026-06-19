from django.test import SimpleTestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import PermissionDenied
from apps.accounts.models.usuario import Usuario
from apps.accounts.constants import EstadoUsuario
from apps.companies.models.empresa import Empresa
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.rol import Rol
from apps.authorization.models.permiso import Permiso
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol_permiso import RolPermiso
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.constants import EstadoUsuarioEmpresa, TipoRol, EstadoRol, TipoPermisoDirecto
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.authorization.services.company_context_service import resolve_user_company_context
from apps.authorization.permissions.drf_permissions import (
    IsAuthenticatedAndActive,
    HasCompanyAccess,
    HasCompanyPermission,
    IsPlatformSuperadmin
)

class AuthorizationModelsSanityTest(SimpleTestCase):
    """
    Sanity tests to verify authorization models configuration.
    """
    def test_models_managed_metadata(self):
        self.assertFalse(UsuarioEmpresa._meta.managed)
        self.assertFalse(Rol._meta.managed)
        self.assertFalse(Permiso._meta.managed)
        self.assertFalse(UsuarioEmpresaRol._meta.managed)
        self.assertFalse(RolPermiso._meta.managed)
        self.assertFalse(UsuarioEmpresaPermiso._meta.managed)

    def test_models_db_table_names(self):
        self.assertEqual(UsuarioEmpresa._meta.db_table, 'pdg"."uep_usuario_empresa')
        self.assertEqual(Rol._meta.db_table, 'pdg"."rol_rol')
        self.assertEqual(Permiso._meta.db_table, 'pdg"."per_permiso')
        self.assertEqual(UsuarioEmpresaRol._meta.db_table, 'pdg"."uer_usuario_empresa_rol')
        self.assertEqual(RolPermiso._meta.db_table, 'pdg"."rpe_rol_permiso')
        self.assertEqual(UsuarioEmpresaPermiso._meta.db_table, 'pdg"."uepr_usuario_empresa_permiso')


class RBACServiceTests(SimpleTestCase):
    """
    Tests calculating effective permissions, checking platform superadmins,
    and resolving company contexts.
    """
    def setUp(self):
        super().setUp()
        self.user = Usuario(id=1, usr_correo="admin@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)

    @patch('apps.authorization.models.usuario_empresa_rol.UsuarioEmpresaRol.objects.using')
    def test_is_platform_superadmin_active(self, mock_uer_using):
        """
        User has active PLATAFORMA SUPERADMIN role assignment.
        """
        mock_uer_using.return_value.filter.return_value.filter.return_value.exists.return_value = True
        self.assertTrue(is_platform_superadmin(self.user))

    @patch('apps.authorization.models.usuario_empresa_rol.UsuarioEmpresaRol.objects.using')
    def test_is_platform_superadmin_inactive(self, mock_uer_using):
        """
        User does not have an active PLATAFORMA SUPERADMIN role assignment.
        """
        mock_uer_using.return_value.filter.return_value.filter.return_value.exists.return_value = False
        self.assertFalse(is_platform_superadmin(self.user))

    @patch('apps.authorization.services.company_context_service.get_user_company_relation')
    def test_resolve_company_context_success(self, mock_get_relation):
        """
        User has active relationship with active company.
        """
        company = Empresa(id=1, nombre_comercial="Company One", estado="ACTIVA", eliminado=False)
        relation = UsuarioEmpresa(usuario=self.user, empresa=company, estado=EstadoUsuarioEmpresa.ACTIVO)
        mock_get_relation.return_value = relation

        resolved = resolve_user_company_context(self.user, 1)
        self.assertEqual(resolved, company)

    @patch('apps.authorization.services.company_context_service.get_user_company_relation')
    def test_resolve_company_context_denied(self, mock_get_relation):
        """
        User does not belong to the company or relation is inactive.
        """
        mock_get_relation.return_value = None
        with self.assertRaises(PermissionDenied):
            resolve_user_company_context(self.user, 1)

    @patch('apps.authorization.services.permission_service.is_platform_superadmin')
    @patch('apps.authorization.services.permission_service.get_user_company_relation')
    @patch('apps.authorization.services.permission_service.get_active_user_company_roles')
    @patch('apps.authorization.services.permission_service.get_user_direct_permissions')
    @patch('apps.authorization.models.rol_permiso.RolPermiso.objects.using')
    def test_calculate_effective_permissions_precedence(
        self, mock_rp_using, mock_get_direct, mock_get_roles, mock_get_relation, mock_is_superadmin
    ):
        """
        Rule: Revocación directa > Concesión directa > Permiso heredado por rol.
        Roles offer: PERM_A, PERM_B.
        Conceder offers: PERM_C.
        Revocar removes: PERM_B.
        Expected effective: PERM_A, PERM_C.
        """
        mock_is_superadmin.return_value = False
        
        company = Empresa(id=1, nombre_comercial="Company One", estado="ACTIVA")
        relation = UsuarioEmpresa(usuario=self.user, empresa=company, estado=EstadoUsuarioEmpresa.ACTIVO)
        mock_get_relation.return_value = relation

        # Active roles
        role = Rol(id=10, codigo="DEV", tipo=TipoRol.EMPRESA)
        user_rol = UsuarioEmpresaRol(usuario_empresa=relation, rol=role)
        mock_get_roles.return_value = [user_rol]

        # RolPermiso lookup yields PERM_A, PERM_B
        mock_rp_using.return_value.filter.return_value.values_list.return_value = ["PERM_A", "PERM_B"]

        # Direct concessions & revocations
        perm_b = Permiso(codigo="PERM_B")
        perm_c = Permiso(codigo="PERM_C")
        exc_b = UsuarioEmpresaPermiso(usuario_empresa=relation, permiso=perm_b, tipo=TipoPermisoDirecto.REVOCAR)
        exc_c = UsuarioEmpresaPermiso(usuario_empresa=relation, permiso=perm_c, tipo=TipoPermisoDirecto.CONCEDER)
        mock_get_direct.return_value = [exc_b, exc_c]

        effective = calculate_effective_permissions(self.user.id, 1)
        
        self.assertIn("PERM_A", effective)
        self.assertIn("PERM_C", effective)
        self.assertNotIn("PERM_B", effective)


class DRFPermissionClassesTests(SimpleTestCase):
    """
    Tests HasCompanyAccess and HasCompanyPermission DRF permission classes.
    """
    def setUp(self):
        super().setUp()
        self.user = Usuario(id=1, usr_correo="user@example.com", estado=EstadoUsuario.ACTIVO, correo_verificado=True)
        self.request = MagicMock()
        self.request.user = self.user
        self.request.headers = {}
        self.view = MagicMock()
        self.view.kwargs = {'emp_id': 1}

    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    def test_has_company_access_normal_user(self, mock_get_relation, mock_is_superadmin):
        mock_is_superadmin.return_value = False
        mock_get_relation.return_value = UsuarioEmpresa()

        perm = HasCompanyAccess()
        self.assertTrue(perm.has_permission(self.request, self.view))

    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    def test_has_company_access_superadmin(self, mock_get_relation, mock_is_superadmin):
        # Platform superadmins don't need relation
        mock_is_superadmin.return_value = True
        mock_get_relation.return_value = None

        perm = HasCompanyAccess()
        self.assertTrue(perm.has_permission(self.request, self.view))

    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    def test_has_company_access_denied(self, mock_get_relation, mock_is_superadmin):
        mock_is_superadmin.return_value = False
        mock_get_relation.return_value = None

        perm = HasCompanyAccess()
        self.assertFalse(perm.has_permission(self.request, self.view))

    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.calculate_effective_permissions')
    def test_has_company_permission_success(self, mock_calc_perms, mock_get_relation, mock_is_superadmin):
        mock_is_superadmin.return_value = False
        mock_get_relation.return_value = UsuarioEmpresa()
        mock_calc_perms.return_value = {"EDICION_CREAR"}
        self.view.required_permission = "EDICION_CREAR"

        perm = HasCompanyPermission()
        self.assertTrue(perm.has_permission(self.request, self.view))

    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.calculate_effective_permissions')
    def test_has_company_permission_denied(self, mock_calc_perms, mock_get_relation, mock_is_superadmin):
        mock_is_superadmin.return_value = False
        mock_get_relation.return_value = UsuarioEmpresa()
        mock_calc_perms.return_value = {"EDICION_CREAR"}
        self.view.required_permission = "EDICION_ELIMINAR"  # Requires delete

        perm = HasCompanyPermission()
        self.assertFalse(perm.has_permission(self.request, self.view))
