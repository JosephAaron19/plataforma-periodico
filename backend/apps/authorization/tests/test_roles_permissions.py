from django.test import SimpleTestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import ValidationError as DRFValidationError
from unittest.mock import patch, MagicMock, ANY
from contextlib import contextmanager
from datetime import timedelta
from django.utils import timezone
import uuid

@contextmanager
def dummy_atomic(using=None, savepoint=True):
    yield

# Models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol import Rol
from apps.authorization.models.permiso import Permiso
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.models.rol_historial import RolHistorial

# Views
from apps.authorization.views.roles_permissions import (
    CompanyRoleListView,
    CompanyPermissionListView,
    MemberRoleListAssignView,
    MemberRoleFinalizeView,
    MemberRoleSetPrimaryView,
    MemberEffectivePermissionListView,
    MemberPermissionGrantView,
    MemberPermissionRevokeView,
    MemberPermissionRemoveExceptionView
)

class CompanyRolesPermissionsTests(SimpleTestCase):
    """
    Test suite for company roles and permissions management views and services.
    Uses SimpleTestCase to avoid hitting the external PostgreSQL database.
    """
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

        # Users and Company mocks
        self.solicitante = Usuario(
            id=1,
            usr_correo="solicitor@example.com",
            nombres="Solicitor",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False
        )
        self.target_user = Usuario(
            id=2,
            usr_correo="target@example.com",
            nombres="Target",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False
        )
        self.company = Empresa(
            id=1,
            ruc="20100000001",
            razon_social="Company One",
            estado="ACTIVA",
            eliminado=False
        )
        self.uep = UsuarioEmpresa(
            id=10,
            usuario=self.target_user,
            empresa=self.company,
            estado="ACTIVO"
        )

        # Global patches to bypass standard permission checks and Celery
        self.sa_patcher = patch('apps.authorization.services.permission_service.is_platform_superadmin', return_value=False)
        self.cp_patcher = patch('apps.authorization.services.permission_service.calculate_effective_permissions', return_value=['ROL_GESTIONAR', 'USUARIO_VER'])
        self.sa_patcher.start()
        self.cp_patcher.start()

        # Specific patches for services to avoid DB calls in SimpleTestCase
        self.grant_sa_patcher = patch('apps.authorization.services.direct_permission_grant_service.is_platform_superadmin', return_value=False)
        self.grant_cp_patcher = patch('apps.authorization.services.direct_permission_grant_service.calculate_effective_permissions', return_value=['EDICION_PUBLICAR', 'ROL_GESTIONAR', 'USUARIO_VER'])
        self.revoke_sa_patcher = patch('apps.authorization.services.direct_permission_revoke_service.is_platform_superadmin', return_value=False)
        self.revoke_cp_patcher = patch('apps.authorization.services.direct_permission_revoke_service.calculate_effective_permissions', return_value=['EDICION_PUBLICAR', 'ROL_GESTIONAR', 'USUARIO_VER'])
        
        self.grant_sa_patcher.start()
        self.grant_cp_patcher.start()
        self.revoke_sa_patcher.start()
        self.revoke_cp_patcher.start()

        # Audit record_event patcher
        self.audit_patcher = patch('apps.audit.services.audit_service.AuditService.record_event')
        self.mock_audit = self.audit_patcher.start()

    def tearDown(self):
        self.sa_patcher.stop()
        self.cp_patcher.stop()
        self.grant_sa_patcher.stop()
        self.grant_cp_patcher.stop()
        self.revoke_sa_patcher.stop()
        self.revoke_cp_patcher.stop()
        self.audit_patcher.stop()
        super().tearDown()

    # 1. GET /api/v1/companies/{emp_id}/roles/
    @patch('apps.authorization.views.roles_permissions.HasAnyCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.roles_permissions.get_available_company_roles')
    def test_list_roles_success(self, mock_get_roles, mock_has_perm):
        mock_get_roles.return_value = Rol.objects.none()
        request = self.factory.get('/api/v1/companies/1/roles/')
        force_authenticate(request, user=self.solicitante)
        
        view = CompanyRoleListView.as_view()
        response = view(request, emp_id=1)
        self.assertEqual(response.status_code, 200)
        mock_get_roles.assert_called_once_with(1)

    # 2. GET /api/v1/companies/{emp_id}/permissions/
    @patch('apps.authorization.views.roles_permissions.HasAnyCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.roles_permissions.get_available_company_permissions')
    def test_list_permissions_success(self, mock_get_perms, mock_has_perm):
        mock_get_perms.return_value = Permiso.objects.none()
        request = self.factory.get('/api/v1/companies/1/permissions/')
        force_authenticate(request, user=self.solicitante)

        view = CompanyPermissionListView.as_view()
        response = view(request, emp_id=1)
        self.assertEqual(response.status_code, 200)
        mock_get_perms.assert_called_once_with(1)

    # 3. GET /api/v1/companies/{emp_id}/members/{uep_id}/roles/ (Success and IDOR)
    @patch('apps.authorization.views.roles_permissions.HasAnyCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.roles_permissions.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.views.roles_permissions.get_member_roles')
    def test_list_member_roles_success(self, mock_get_member_roles, mock_uep_using, mock_has_perm):
        mock_uep_using.return_value.get.return_value = self.uep
        mock_get_member_roles.return_value = UsuarioEmpresaRol.objects.none()

        request = self.factory.get('/api/v1/companies/1/members/10/roles/')
        force_authenticate(request, user=self.solicitante)

        view = MemberRoleListAssignView.as_view()
        response = view(request, emp_id=1, uep_id=10)
        self.assertEqual(response.status_code, 200)
        mock_get_member_roles.assert_called_once_with(10, 1)

    @patch('apps.authorization.views.roles_permissions.HasAnyCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.roles_permissions.UsuarioEmpresa.objects.using')
    def test_list_member_roles_idor_blocked(self, mock_uep_using, mock_has_perm):
        # Target member belongs to company 2, but request is for company 1
        mock_uep_using.return_value.get.side_effect = UsuarioEmpresa.DoesNotExist

        request = self.factory.get('/api/v1/companies/1/members/10/roles/')
        force_authenticate(request, user=self.solicitante)

        view = MemberRoleListAssignView.as_view()
        response = view(request, emp_id=1, uep_id=10)
        self.assertEqual(response.status_code, 404)

    # 4. POST /api/v1/companies/{emp_id}/members/{uep_id}/roles/ (Assign Role service and view)
    @patch('apps.authorization.services.role_assignment_service.Rol.objects.using')
    @patch('apps.authorization.services.role_assignment_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.role_assignment_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.role_assignment_service.RolHistorial.save')
    @patch('apps.authorization.services.role_assignment_service.transaction.atomic', side_effect=dummy_atomic)
    def test_assign_role_success(self, mock_atomic, mock_historial_save, mock_uer_using, mock_uep_using, mock_rol_using):
        from apps.authorization.services.role_assignment_service import assign_role_to_member

        role = Rol(id=101, codigo="EDITOR", nombre="Editor", tipo="EMPRESA", estado="ACTIVO")
        mock_rol_using.return_value.get.return_value = role
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = self.uep

        # No existing assignment
        mock_uer_using.return_value.select_for_update.return_value.filter.return_value.first.return_value = None

        with patch('apps.authorization.models.usuario_empresa_rol.UsuarioEmpresaRol.save') as mock_uer_save:
            uer = assign_role_to_member(
                uep_id=10,
                emp_id=1,
                role_code="EDITOR",
                is_primary=True,
                solicitante=self.solicitante
            )
            self.assertIsNotNone(uer)
            mock_uer_save.assert_called_once()
            mock_historial_save.assert_called_once()
            self.mock_audit.assert_called_once_with(
                usuario=self.solicitante,
                emp_id=1,
                modulo="M04",
                accion="ROL_ASIGNADO",
                entidad="UsuarioEmpresaRol",
                entidad_id=ANY,
                valores_anteriores=None,
                valores_nuevos={"estado": "ACTIVO", "rol": "EDITOR", "es_principal": True},
                resultado="EXITOSO",
                motivo=ANY,
                ip_address=ANY,
                user_agent=ANY,
                throw_on_error=False
            )

    @patch('apps.authorization.services.role_assignment_service.Rol.objects.using')
    @patch('apps.authorization.services.role_assignment_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.role_assignment_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.role_assignment_service.transaction.atomic', side_effect=dummy_atomic)
    def test_assign_role_duplicate_active_blocked(self, mock_atomic, mock_uer_using, mock_uep_using, mock_rol_using):
        from apps.authorization.services.role_assignment_service import assign_role_to_member

        role = Rol(id=101, codigo="EDITOR", nombre="Editor", tipo="EMPRESA", estado="ACTIVO")
        mock_rol_using.return_value.get.return_value = role
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = self.uep

        # Existing active assignment
        existing_uer = UsuarioEmpresaRol(usuario_empresa=self.uep, rol=role, estado="ACTIVO")
        mock_uer_using.return_value.select_for_update.return_value.filter.return_value.first.return_value = existing_uer

        with self.assertRaises(DjangoValidationError) as ctx:
            assign_role_to_member(
                uep_id=10,
                emp_id=1,
                role_code="EDITOR",
                solicitante=self.solicitante
            )
        self.assertIn("El miembro ya posee este rol asignado y activo.", str(ctx.exception))

    @patch('apps.authorization.services.role_assignment_service.Rol.objects.using')
    @patch('apps.authorization.services.role_assignment_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.role_assignment_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.role_assignment_service.RolHistorial.save')
    @patch('apps.authorization.services.role_assignment_service.transaction.atomic', side_effect=dummy_atomic)
    def test_assign_role_reactivate_inactive(self, mock_atomic, mock_historial_save, mock_uer_using, mock_uep_using, mock_rol_using):
        from apps.authorization.services.role_assignment_service import assign_role_to_member

        role = Rol(id=101, codigo="EDITOR", nombre="Editor", tipo="EMPRESA", estado="ACTIVO")
        mock_rol_using.return_value.get.return_value = role
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = self.uep

        # Existing inactive assignment (FINALIZADO)
        existing_uer = UsuarioEmpresaRol(usuario_empresa=self.uep, rol=role, estado="FINALIZADO")
        existing_uer.save = MagicMock()
        mock_uer_using.return_value.select_for_update.return_value.filter.return_value.first.return_value = existing_uer

        uer = assign_role_to_member(
            uep_id=10,
            emp_id=1,
            role_code="EDITOR",
            solicitante=self.solicitante
        )
        self.assertEqual(uer.estado, "ACTIVO")
        existing_uer.save.assert_called_once()

    # 5. POST /api/v1/companies/{emp_id}/members/{uep_id}/roles/{assignment_id}/finalize/
    @patch('apps.authorization.services.role_finalize_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.role_finalize_service.RolHistorial.save')
    @patch('apps.authorization.services.role_finalize_service.transaction.atomic', side_effect=dummy_atomic)
    def test_finalize_role_success(self, mock_atomic, mock_historial_save, mock_uer_using):
        from apps.authorization.services.role_finalize_service import finalize_member_role

        role = Rol(id=101, codigo="EDITOR", nombre="Editor", tipo="EMPRESA", estado="ACTIVO")
        uer = UsuarioEmpresaRol(id=50, usuario_empresa=self.uep, rol=role, estado="ACTIVO", es_principal=True)
        uer.save = MagicMock()
        mock_uer_using.return_value.select_for_update.return_value.get.return_value = uer

        res_uer = finalize_member_role(
            uep_id=10,
            emp_id=1,
            uer_id=50,
            solicitante=self.solicitante,
            motivo="Finalización por retiro"
        )
        self.assertEqual(res_uer.estado, "FINALIZADO")
        self.assertFalse(res_uer.es_principal)
        uer.save.assert_called_once()
        mock_historial_save.assert_called_once()

    @patch('apps.authorization.services.role_finalize_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.role_finalize_service.transaction.atomic', side_effect=dummy_atomic)
    def test_finalize_last_admin_role_blocked(self, mock_atomic, mock_uer_using):
        from apps.authorization.services.role_finalize_service import finalize_member_role

        role_admin = Rol(id=102, codigo="ADMIN_EMPRESA", nombre="Administrador", tipo="EMPRESA", estado="ACTIVO")
        uer = UsuarioEmpresaRol(id=50, usuario_empresa=self.uep, rol=role_admin, estado="ACTIVO")
        mock_uer_using.return_value.select_for_update.return_value.get.return_value = uer

        # Mock query count of other active admins returning no results
        mock_other_admins_qs = MagicMock()
        mock_other_admins_qs.filter.return_value.exclude.return_value.exists.return_value = False
        mock_uer_using.return_value.select_for_update.return_value.filter.return_value = mock_other_admins_qs

        with self.assertRaises(DjangoValidationError) as ctx:
            finalize_member_role(
                uep_id=10,
                emp_id=1,
                uer_id=50,
                solicitante=self.solicitante,
                motivo="Finalizar administrador"
            )
        self.assertIn("No se puede finalizar el último rol administrador activo de la empresa.", str(ctx.exception))
        # Verify block is audited
        self.mock_audit.assert_called_once_with(
            usuario=self.solicitante,
            emp_id=1,
            modulo="M04",
            accion="ULTIMO_ADMINISTRADOR_PROTEGIDO",
            entidad="UsuarioEmpresaRol",
            entidad_id="50",
            valores_anteriores={"estado": "ACTIVO"},
            valores_nuevos=None,
            resultado="RECHAZADO",
            motivo=ANY,
            ip_address=ANY,
            user_agent=ANY,
            throw_on_error=False
        )

    # 6. POST /api/v1/companies/{emp_id}/members/{uep_id}/roles/{assignment_id}/set-primary/
    @patch('apps.authorization.services.role_primary_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.role_primary_service.RolHistorial.save')
    @patch('apps.authorization.services.role_primary_service.transaction.atomic', side_effect=dummy_atomic)
    def test_set_primary_role_success(self, mock_atomic, mock_historial_save, mock_uer_using):
        from apps.authorization.services.role_primary_service import set_member_primary_role

        role_editor = Rol(id=101, codigo="EDITOR", nombre="Editor", tipo="EMPRESA", estado="ACTIVO")
        uer_target = UsuarioEmpresaRol(id=50, usuario_empresa=self.uep, rol=role_editor, estado="ACTIVO", es_principal=False, fecha_inicio=timezone.now() - timedelta(days=1))
        uer_target.save = MagicMock()

        role_viewer = Rol(id=103, codigo="LECTOR", nombre="Lector", tipo="LECTOR", estado="ACTIVO")
        uer_old_primary = UsuarioEmpresaRol(id=51, usuario_empresa=self.uep, rol=role_viewer, estado="ACTIVO", es_principal=True)
        uer_old_primary.save = MagicMock()

        # Mock select_for_update chains
        mock_uer_using.return_value.select_for_update.return_value.get.return_value = uer_target
        mock_uer_using.return_value.select_for_update.return_value.filter.return_value = [uer_target, uer_old_primary]

        res = set_member_primary_role(
            uep_id=10,
            emp_id=1,
            uer_id=50,
            solicitante=self.solicitante
        )
        self.assertTrue(res.es_principal)
        self.assertFalse(uer_old_primary.es_principal)
        uer_target.save.assert_called_once()
        uer_old_primary.save.assert_called_once()

    # 7. GET /api/v1/companies/{emp_id}/members/{uep_id}/permissions/
    @patch('apps.authorization.views.roles_permissions.HasAnyCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.roles_permissions.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.views.roles_permissions.calculate_effective_permissions')
    @patch('apps.authorization.views.roles_permissions.Permiso.objects.using')
    @patch('apps.authorization.views.roles_permissions.get_user_direct_permissions')
    def test_list_effective_permissions_success(self, mock_get_direct, mock_perm_using, mock_calc_perms, mock_uep_using, mock_has_perm):
        mock_uep_using.return_value.get.return_value = self.uep
        mock_calc_perms.return_value = {"EDICION_CREAR", "EDICION_PUBLICAR"}

        perm_crear = Permiso(codigo="EDICION_CREAR", nombre="Crear Edición", estado="ACTIVO")
        perm_publicar = Permiso(codigo="EDICION_PUBLICAR", nombre="Publicar Edición", estado="ACTIVO")
        mock_perm_using.return_value.filter.return_value = [perm_crear, perm_publicar]

        # Simulating that EDICION_PUBLICAR is a direct concession
        dp_mock = MagicMock()
        dp_mock.permiso.codigo = "EDICION_PUBLICAR"
        dp_mock.tipo = "CONCEDER"
        mock_get_direct.return_value = [dp_mock]

        request = self.factory.get('/api/v1/companies/1/members/10/permissions/')
        force_authenticate(request, user=self.solicitante)

        view = MemberEffectivePermissionListView.as_view()
        response = view(request, emp_id=1, uep_id=10)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data), 2)
        
        # Verify origins mapping
        crear_data = next(x for x in data if x['code'] == "EDICION_CREAR")
        publicar_data = next(x for x in data if x['code'] == "EDICION_PUBLICAR")
        self.assertEqual(crear_data['origen'], 'ROL')
        self.assertEqual(publicar_data['origen'], 'CONCESION_DIRECTA')

    # 8. POST /api/v1/companies/{emp_id}/members/{uep_id}/permissions/grant/
    @patch('apps.authorization.services.direct_permission_grant_service.Permiso.objects.using')
    @patch('apps.authorization.services.direct_permission_grant_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.direct_permission_grant_service.UsuarioEmpresaPermiso.objects.using')
    @patch('apps.authorization.services.direct_permission_grant_service.RolHistorial.save')
    @patch('apps.authorization.services.direct_permission_grant_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.direct_permission_grant_service.calculate_effective_permissions')
    def test_grant_direct_permission_success(self, mock_calc_perms, mock_atomic, mock_historial_save, mock_uepr_using, mock_uep_using, mock_perm_using):
        from apps.authorization.services.direct_permission_grant_service import grant_direct_permission

        perm = Permiso(id=201, codigo="EDICION_PUBLICAR", nombre="Publicar", estado="ACTIVO")
        mock_perm_using.return_value.get.return_value = perm
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = self.uep
        
        # Requester possesses this permission
        mock_calc_perms.return_value = {"EDICION_PUBLICAR"}
        # No existing concession row
        mock_uepr_using.return_value.select_for_update.return_value.filter.return_value.first.return_value = None

        with patch('apps.authorization.models.usuario_empresa_permiso.UsuarioEmpresaPermiso.save') as mock_uepr_save:
            uepr = grant_direct_permission(
                uep_id=10,
                emp_id=1,
                permission_code="EDICION_PUBLICAR",
                motivo="Habilitación temporal",
                solicitante=self.solicitante
            )
            self.assertIsNotNone(uepr)
            mock_uepr_save.assert_called_once()
            mock_historial_save.assert_called_once()
            self.mock_audit.assert_called_once_with(
                usuario=self.solicitante,
                emp_id=1,
                modulo="M04",
                accion="PERMISO_DIRECTO_CONCEDIDO",
                entidad="UsuarioEmpresaPermiso",
                entidad_id=ANY,
                valores_anteriores=None,
                valores_nuevos={"tipo": "CONCEDER", "permiso": "EDICION_PUBLICAR"},
                resultado="EXITOSO",
                motivo=ANY,
                ip_address=ANY,
                user_agent=ANY,
                throw_on_error=False
            )

    @patch('apps.authorization.services.direct_permission_grant_service.Permiso.objects.using')
    @patch('apps.authorization.services.direct_permission_grant_service.calculate_effective_permissions')
    def test_grant_direct_permission_privilege_escalation_blocked(self, mock_calc_perms, mock_perm_using):
        from apps.authorization.services.direct_permission_grant_service import grant_direct_permission

        perm = Permiso(id=201, codigo="EDICION_PUBLICAR", nombre="Publicar", estado="ACTIVO")
        mock_perm_using.return_value.get.return_value = perm

        # Requester DOES NOT possess this permission
        mock_calc_perms.return_value = {"USUARIO_VER"}

        with self.assertRaises(DjangoValidationError) as ctx:
            grant_direct_permission(
                uep_id=10,
                emp_id=1,
                permission_code="EDICION_PUBLICAR",
                motivo="Intento de escalar privilegios",
                solicitante=self.solicitante
            )
        self.assertIn("No puedes conceder un permiso que tú mismo no posees.", str(ctx.exception))
        # Verify escalation block is audited
        self.mock_audit.assert_called_once_with(
            usuario=self.solicitante,
            emp_id=1,
            modulo="M04",
            accion="ESCALAMIENTO_PRIVILEGIOS_DENEGADO",
            entidad="UsuarioEmpresaPermiso",
            entidad_id=None,
            valores_anteriores=None,
            valores_nuevos={"requested_permission": "EDICION_PUBLICAR"},
            resultado="RECHAZADO",
            motivo=ANY,
            ip_address=ANY,
            user_agent=ANY,
            throw_on_error=False
        )

    # 9. POST /api/v1/companies/{emp_id}/members/{uep_id}/permissions/revoke/
    @patch('apps.authorization.services.direct_permission_revoke_service.Permiso.objects.using')
    @patch('apps.authorization.services.direct_permission_revoke_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.direct_permission_revoke_service.UsuarioEmpresaPermiso.objects.using')
    @patch('apps.authorization.services.direct_permission_revoke_service.RolHistorial.save')
    @patch('apps.authorization.services.direct_permission_revoke_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.direct_permission_revoke_service.calculate_effective_permissions')
    def test_revoke_direct_permission_success(self, mock_calc_perms, mock_atomic, mock_historial_save, mock_uepr_using, mock_uep_using, mock_perm_using):
        from apps.authorization.services.direct_permission_revoke_service import revoke_direct_permission

        perm = Permiso(id=201, codigo="EDICION_PUBLICAR", nombre="Publicar", estado="ACTIVO")
        mock_perm_using.return_value.get.return_value = perm
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = self.uep
        
        # Requester possesses this permission
        mock_calc_perms.return_value = {"EDICION_PUBLICAR"}
        # No existing concession row
        mock_uepr_using.return_value.select_for_update.return_value.filter.return_value.first.return_value = None

        with patch('apps.authorization.models.usuario_empresa_permiso.UsuarioEmpresaPermiso.save') as mock_uepr_save:
            uepr = revoke_direct_permission(
                uep_id=10,
                emp_id=1,
                permission_code="EDICION_PUBLICAR",
                motivo="Revocación de seguridad",
                solicitante=self.solicitante
            )
            self.assertIsNotNone(uepr)
            mock_uepr_save.assert_called_once()
            mock_historial_save.assert_called_once()
            self.mock_audit.assert_called_once_with(
                usuario=self.solicitante,
                emp_id=1,
                modulo="M04",
                accion="PERMISO_DIRECTO_REVOCADO",
                entidad="UsuarioEmpresaPermiso",
                entidad_id=ANY,
                valores_anteriores=None,
                valores_nuevos={"tipo": "REVOCAR", "permiso": "EDICION_PUBLICAR"},
                resultado="EXITOSO",
                motivo=ANY,
                ip_address=ANY,
                user_agent=ANY,
                throw_on_error=False
            )

    # 10. DELETE /api/v1/companies/{emp_id}/members/{uep_id}/permissions/{permission_code}/exception/
    @patch('apps.authorization.services.direct_permission_remove_service.Permiso.objects.using')
    @patch('apps.authorization.services.direct_permission_remove_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.direct_permission_remove_service.UsuarioEmpresaPermiso.objects.using')
    @patch('apps.authorization.services.direct_permission_remove_service.RolHistorial.save')
    @patch('apps.authorization.services.direct_permission_remove_service.transaction.atomic', side_effect=dummy_atomic)
    def test_remove_permission_exception_success(self, mock_atomic, mock_historial_save, mock_uepr_using, mock_uep_using, mock_perm_using):
        from apps.authorization.services.direct_permission_remove_service import remove_direct_permission_exception

        perm = Permiso(id=201, codigo="EDICION_PUBLICAR", nombre="Publicar", estado="ACTIVO")
        mock_perm_using.return_value.get.return_value = perm
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = self.uep

        uepr = UsuarioEmpresaPermiso(id=301, usuario_empresa=self.uep, permiso=perm, tipo="CONCEDER", estado=True)
        uepr.save = MagicMock()
        mock_uepr_using.return_value.select_for_update.return_value.get.return_value = uepr

        res_uepr = remove_direct_permission_exception(
            uep_id=10,
            emp_id=1,
            permission_code="EDICION_PUBLICAR",
            solicitante=self.solicitante
        )
        self.assertFalse(res_uepr.estado)
        self.assertIsNotNone(res_uepr.fecha_fin)
        uepr.save.assert_called_once()
        mock_historial_save.assert_called_once()
        self.mock_audit.assert_called_once_with(
            usuario=self.solicitante,
            emp_id=1,
            modulo="M04",
            accion="EXCEPCION_PERMISO_RETIRADA",
            entidad="UsuarioEmpresaPermiso",
            entidad_id="301",
            valores_anteriores={"tipo": "CONCEDER", "estado": True},
            valores_nuevos={"estado": False},
            resultado="EXITOSO",
            motivo=ANY,
            ip_address=ANY,
            user_agent=ANY,
            throw_on_error=False
        )

    # 11. Platform-exclusive permissions block
    @patch('apps.authorization.services.direct_permission_grant_service.Permiso.objects.using')
    def test_grant_platform_permission_blocked(self, mock_perm_using):
        from apps.authorization.services.direct_permission_grant_service import grant_direct_permission

        perm = Permiso(id=201, codigo="EMPRESA_GESTIONAR", nombre="Manage Companies", estado="ACTIVO")
        mock_perm_using.return_value.get.return_value = perm

        with self.assertRaises(DjangoValidationError) as ctx:
            grant_direct_permission(
                uep_id=10,
                emp_id=1,
                permission_code="EMPRESA_GESTIONAR",
                motivo="Otorgar gestion de empresas",
                solicitante=self.solicitante
            )
        self.assertIn("No se pueden conceder permisos exclusivos de la plataforma a nivel empresarial.", str(ctx.exception))
