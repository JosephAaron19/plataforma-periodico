from django.test import SimpleTestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch, MagicMock
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
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.rol import Rol

# Views
from apps.authorization.views.invitations import (
    CompanyInvitationListCreateView,
    CompanyInvitationResendView,
    CompanyInvitationRevokeView,
    InvitationAcceptView
)
from apps.authorization.views.members import (
    CompanyMemberListView,
    CompanyMemberDetailView,
    CompanyMemberSuspendView,
    CompanyMemberReactivateView
)

class CompanyInvitationsViewsTest(SimpleTestCase):
    """
    Test suite for company invitations and members views using SimpleTestCase and mocks.
    """
    def setUp(self):
        self.factory = APIRequestFactory()
        
        self.user = Usuario(
            id=10,
            usr_correo="manager@example.com",
            nombres="Manager",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False
        )
        self.company = Empresa(id=1, ruc="20100000001", razon_social="Company 1", estado="ACTIVA")

        # Global patches to prevent database query triggers during SimpleTestCase executions
        modules_to_patch = [
            'apps.authorization.services.permission_service',
            'apps.authorization.permissions.drf_permissions',
            'apps.authorization.services.invitation_create_service',
            'apps.authorization.services.invitation_resend_service',
            'apps.authorization.services.invitation_revoke_service',
            'apps.authorization.services.member_suspend_service',
            'apps.authorization.services.member_reactivate_service',
        ]
        self.patchers = []
        for m in modules_to_patch:
            p_sa = patch(f'{m}.is_platform_superadmin', return_value=False)
            p_cp = patch(f'{m}.calculate_effective_permissions', return_value=['USUARIO_GESTIONAR', 'USUARIO_VER'])
            self.patchers.extend([p_sa, p_cp])
            p_sa.start()
            p_cp.start()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    # 1. CompanyInvitationListCreateView GET
    @patch('apps.authorization.views.invitations.HasCompanyAccess.has_permission', return_value=True)
    @patch('apps.authorization.views.invitations.get_company_invitations_queryset')
    def test_list_invitations_success(self, mock_get_queryset, mock_has_access):
        mock_get_queryset.return_value = InvitacionUsuario.objects.none()
        
        request = self.factory.get('/api/v1/companies/1/invitations/')
        force_authenticate(request, user=self.user)
        
        view = CompanyInvitationListCreateView.as_view()
        response = view(request, emp_id=1)
        
        self.assertEqual(response.status_code, 200)
        mock_get_queryset.assert_called_once_with(1)

    # 2. CompanyInvitationListCreateView POST
    @patch('apps.authorization.views.invitations.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.invitations.create_company_invitation')
    def test_create_invitation_success(self, mock_create, mock_has_perm):
        mock_inv = InvitacionUsuario(
            id=uuid.uuid4(),
            correo="newuser@example.com",
            estado="PENDIENTE",
            empresa=self.company,
            rol=Rol(codigo="EDITOR", nombre="Editor")
        )
        mock_create.return_value = mock_inv
        
        data = {
            "email": "newuser@example.com",
            "role_code": "EDITOR",
            "mensaje": "Welcome!"
        }
        request = self.factory.post('/api/v1/companies/1/invitations/', data)
        force_authenticate(request, user=self.user)
        
        view = CompanyInvitationListCreateView.as_view()
        response = view(request, emp_id=1)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['correo'], "newuser@example.com")
        self.assertEqual(response.data['estado'], "PENDIENTE")
        mock_create.assert_called_once()

    @patch('apps.authorization.views.invitations.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.invitations.create_company_invitation')
    def test_create_invitation_error(self, mock_create, mock_has_perm):
        mock_create.side_effect = DjangoValidationError("El usuario ya es un miembro activo.")
        
        data = {
            "email": "existing@example.com",
            "role_code": "EDITOR"
        }
        request = self.factory.post('/api/v1/companies/1/invitations/', data)
        force_authenticate(request, user=self.user)
        
        view = CompanyInvitationListCreateView.as_view()
        response = view(request, emp_id=1)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("El usuario ya es un miembro activo.", response.data[0])

    # 3. CompanyInvitationResendView
    @patch('apps.authorization.views.invitations.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.invitations.resend_company_invitation')
    def test_resend_invitation_success(self, mock_resend, mock_has_perm):
        inv_id = str(uuid.uuid4())
        mock_inv = InvitacionUsuario(
            id=inv_id,
            correo="newuser@example.com",
            estado="REENVIADA",
            empresa=self.company,
            rol=Rol(codigo="EDITOR", nombre="Editor")
        )
        mock_resend.return_value = mock_inv
        
        request = self.factory.post(f'/api/v1/companies/1/invitations/{inv_id}/resend/', {})
        force_authenticate(request, user=self.user)
        
        view = CompanyInvitationResendView.as_view()
        response = view(request, emp_id=1, invitation_id=inv_id)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado'], "REENVIADA")
        mock_resend.assert_called_once()

    # 4. CompanyInvitationRevokeView
    @patch('apps.authorization.views.invitations.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.invitations.revoke_company_invitation')
    def test_revoke_invitation_success(self, mock_revoke, mock_has_perm):
        inv_id = str(uuid.uuid4())
        mock_inv = InvitacionUsuario(
            id=inv_id,
            correo="newuser@example.com",
            estado="REVOCADA",
            empresa=self.company,
            rol=Rol(codigo="EDITOR", nombre="Editor")
        )
        mock_revoke.return_value = mock_inv
        
        request = self.factory.post(f'/api/v1/companies/1/invitations/{inv_id}/revoke/', {})
        force_authenticate(request, user=self.user)
        
        view = CompanyInvitationRevokeView.as_view()
        response = view(request, emp_id=1, invitation_id=inv_id)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado'], "REVOCADA")
        mock_revoke.assert_called_once()

    # 5. InvitationAcceptView (Public)
    @patch('apps.authorization.views.invitations.accept_company_invitation')
    def test_accept_invitation_success(self, mock_accept):
        mock_uep = MagicMock(spec=UsuarioEmpresa)
        mock_uep.id = 45
        mock_uep.usuario = self.user
        mock_uep.empresa = self.company
        mock_uep.estado = "ACTIVO"
        mock_uep.es_principal = True
        mock_uep.fecha_asignacion = None
        mock_uep.fecha_finalizacion = None
        mock_uep.asignado_por = self.user
        mock_uep.motivo = "Invitación aceptada"
        mock_uep.fecha_actualizacion = None
        
        # Mock the prefetch relation returning Rol
        mock_uer = MagicMock()
        mock_uer.rol.codigo = "EDITOR"
        mock_uer.rol.nombre = "Editor"
        mock_uer.estado = "ACTIVO"
        mock_uer.es_principal = True
        
        mock_uep.roles_asignados.filter.return_value = [mock_uer]
        mock_accept.return_value = mock_uep
        
        data = {
            "token": "plain-text-token-value-abc"
        }
        request = self.factory.post('/api/v1/auth/invitations/accept/', data)
        # No authentication required
        
        view = InvitationAcceptView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado'], "ACTIVO")
        self.assertEqual(response.data['roles'][0]['rol_codigo'], "EDITOR")
        mock_accept.assert_called_once()

    # 6. CompanyMemberListView
    @patch('apps.authorization.views.members.HasCompanyAccess.has_permission', return_value=True)
    @patch('apps.authorization.views.members.get_company_members_queryset')
    def test_list_members_success(self, mock_get_queryset, mock_has_access):
        mock_get_queryset.return_value = UsuarioEmpresa.objects.none()
        
        request = self.factory.get('/api/v1/companies/1/members/')
        force_authenticate(request, user=self.user)
        
        view = CompanyMemberListView.as_view()
        response = view(request, emp_id=1)
        
        self.assertEqual(response.status_code, 200)
        mock_get_queryset.assert_called_once_with(1)

    # 7. CompanyMemberDetailView
    @patch('apps.authorization.views.members.HasCompanyAccess.has_permission', return_value=True)
    @patch('apps.authorization.views.members.get_company_members_queryset')
    def test_detail_member_success(self, mock_get_queryset, mock_has_access):
        mock_uep = MagicMock(spec=UsuarioEmpresa)
        mock_uep.id = 12
        mock_uep.usuario = self.user
        mock_uep.empresa = self.company
        mock_uep.estado = "ACTIVO"
        mock_uep.es_principal = True
        mock_uep.fecha_asignacion = None
        mock_uep.fecha_finalizacion = None
        mock_uep.asignado_por = self.user
        mock_uep.motivo = "Active"
        mock_uep.fecha_actualizacion = None
        
        mock_uer = MagicMock()
        mock_uer.rol.codigo = "EDITOR"
        mock_uer.rol.nombre = "Editor"
        mock_uer.estado = "ACTIVO"
        mock_uer.es_principal = True
        
        mock_uep.roles_asignados.filter.return_value = [mock_uer]
        
        mock_qs = MagicMock()
        mock_qs.get.return_value = mock_uep
        mock_get_queryset.return_value = mock_qs
        
        request = self.factory.get('/api/v1/companies/1/members/12/')
        force_authenticate(request, user=self.user)
        
        view = CompanyMemberDetailView.as_view()
        response = view(request, emp_id=1, uep_id=12)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], 12)
        mock_qs.get.assert_called_once_with(id=12)

    @patch('apps.authorization.views.members.HasCompanyAccess.has_permission', return_value=True)
    @patch('apps.authorization.views.members.get_company_members_queryset')
    def test_detail_member_not_found(self, mock_get_queryset, mock_has_access):
        mock_qs = MagicMock()
        mock_qs.get.side_effect = UsuarioEmpresa.DoesNotExist
        mock_get_queryset.return_value = mock_qs
        
        request = self.factory.get('/api/v1/companies/1/members/999/')
        force_authenticate(request, user=self.user)
        
        view = CompanyMemberDetailView.as_view()
        response = view(request, emp_id=1, uep_id=999)
        
        self.assertEqual(response.status_code, 404)

    # 8. CompanyMemberSuspendView
    @patch('apps.authorization.views.members.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.members.suspend_company_member')
    def test_suspend_member_success(self, mock_suspend, mock_has_perm):
        mock_uep = MagicMock(spec=UsuarioEmpresa)
        mock_uep.id = 12
        mock_uep.usuario = self.user
        mock_uep.empresa = self.company
        mock_uep.estado = "SUSPENDIDO"
        mock_uep.es_principal = True
        mock_uep.fecha_asignacion = None
        mock_uep.fecha_finalizacion = None
        mock_uep.asignado_por = self.user
        mock_uep.motivo = "Comportamiento inadecuado"
        mock_uep.fecha_actualizacion = None
        
        mock_uer = MagicMock()
        mock_uer.rol.codigo = "EDITOR"
        mock_uer.rol.nombre = "Editor"
        mock_uer.estado = "SUSPENDIDO"
        mock_uer.es_principal = True
        
        mock_uep.roles_asignados.filter.return_value = [mock_uer]
        mock_suspend.return_value = mock_uep
        
        data = {
            "motivo": "Comportamiento inadecuado"
        }
        request = self.factory.post('/api/v1/companies/1/members/12/suspend/', data)
        force_authenticate(request, user=self.user)
        
        view = CompanyMemberSuspendView.as_view()
        response = view(request, emp_id=1, uep_id=12)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado'], "SUSPENDIDO")
        mock_suspend.assert_called_once()

    # 9. CompanyMemberReactivateView
    @patch('apps.authorization.views.members.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.members.reactivate_company_member')
    def test_reactivate_member_success(self, mock_reactivate, mock_has_perm):
        mock_uep = MagicMock(spec=UsuarioEmpresa)
        mock_uep.id = 12
        mock_uep.usuario = self.user
        mock_uep.empresa = self.company
        mock_uep.estado = "ACTIVO"
        mock_uep.es_principal = True
        mock_uep.fecha_asignacion = None
        mock_uep.fecha_finalizacion = None
        mock_uep.asignado_por = self.user
        mock_uep.motivo = "Reactivación de miembro"
        mock_uep.fecha_actualizacion = None
        
        mock_uer = MagicMock()
        mock_uer.rol.codigo = "EDITOR"
        mock_uer.rol.nombre = "Editor"
        mock_uer.estado = "ACTIVO"
        mock_uer.es_principal = True
        
        mock_uep.roles_asignados.filter.return_value = [mock_uer]
        mock_reactivate.return_value = mock_uep
        
        request = self.factory.post('/api/v1/companies/1/members/12/reactivate/', {})
        force_authenticate(request, user=self.user)
        
        view = CompanyMemberReactivateView.as_view()
        response = view(request, emp_id=1, uep_id=12)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado'], "ACTIVO")
        mock_reactivate.assert_called_once()

    # 10. Service & Security Logical Tests
    
    # 10.1 Existing user accepts invitation - wrong or missing authentication
    @patch('apps.authorization.services.invitation_accept_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.invitation_accept_service.InvitacionUsuario.objects.using')
    @patch('apps.authorization.services.invitation_accept_service.Usuario.objects.using')
    def test_accept_invitation_existing_user_wrong_or_no_auth(self, mock_user_using, mock_inv_using, mock_atomic):
        from apps.authorization.services.invitation_accept_service import accept_company_invitation
        
        # Mock invitation
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'existing@example.com'
        mock_inv.fecha_expiracion = timezone.now() + timedelta(hours=24)
        mock_inv_using.return_value.select_for_update.return_value.get.return_value = mock_inv
        
        # Mock existing user
        mock_existing_user = Usuario(id=20, usr_correo='existing@example.com', estado='ACTIVO')
        mock_user_using.return_value.filter.return_value.first.return_value = mock_existing_user
        
        # Scenario A: No logged in user (anonymous)
        with self.assertRaises(DjangoValidationError) as ctx:
            accept_company_invitation(plain_token="token-abc", logged_in_user=None)
        self.assertIn("El token de invitación es inválido, ha expirado o ya fue procesado.", str(ctx.exception))
        
        # Scenario B: Logged in with different email
        wrong_user = Usuario(id=30, usr_correo='wrong@example.com', estado='ACTIVO')
        with self.assertRaises(DjangoValidationError) as ctx:
            accept_company_invitation(plain_token="token-abc", logged_in_user=wrong_user)
        self.assertIn("El token de invitación es inválido, ha expirado o ya fue procesado.", str(ctx.exception))

        # Scenario C: Passing password parameter for existing user should also fail
        with self.assertRaises(DjangoValidationError) as ctx:
            accept_company_invitation(plain_token="token-abc", password="some-password", logged_in_user=mock_existing_user)
        self.assertIn("El token de invitación es inválido, ha expirado o ya fue procesado.", str(ctx.exception))

    # 10.2 Expired token accepting
    @patch('apps.authorization.services.invitation_accept_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.invitation_accept_service.InvitacionUsuario.objects.using')
    def test_accept_invitation_expired_token(self, mock_inv_using, mock_atomic):
        from apps.authorization.services.invitation_accept_service import accept_company_invitation
        
        # Mock expired invitation
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.fecha_expiracion = timezone.now() - timedelta(hours=1) # in the past
        mock_inv_using.return_value.select_for_update.return_value.get.return_value = mock_inv
        
        with self.assertRaises(DjangoValidationError) as ctx:
            accept_company_invitation(plain_token="token-abc")
        self.assertIn("El token de invitación ha expirado.", str(ctx.exception))
        self.assertEqual(mock_inv.estado, 'VENCIDA')
        mock_inv.save.assert_called_once()

    # 10.3 Create invitation to a Platform Role is blocked
    @patch('apps.authorization.services.invitation_create_service.is_platform_superadmin', return_value=True)
    @patch('apps.authorization.services.invitation_create_service.Empresa.objects.using')
    @patch('apps.authorization.services.invitation_create_service.Rol.objects.using')
    def test_create_invitation_platform_role_blocked(self, mock_rol_using, mock_empresa_using, mock_superadmin):
        from apps.authorization.services.invitation_create_service import create_company_invitation
        
        mock_empresa_using.return_value.get.return_value = self.company
        
        # Mock a PLATFORMA role
        platform_rol = Rol(codigo='SUPERADMIN', tipo='PLATFORMA', estado='ACTIVO')
        mock_rol_using.return_value.get.return_value = platform_rol
        
        with self.assertRaises(DjangoValidationError) as ctx:
            create_company_invitation(
                empresa_id=1,
                email="test@example.com",
                role_code="SUPERADMIN",
                invitado_por=self.user
            )
        self.assertIn("Solo se pueden asignar roles de tipo empresarial por invitación.", str(ctx.exception))

    # 10.4 Rate limit check for resending (cooldown interval)
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    def test_resend_invitation_rate_limit(self, mock_inv_using):
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        # Mock invitation recently sent (cooldown < 60s)
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=30) # 30s ago
        mock_inv_using.return_value.get.return_value = mock_inv
        
        with self.assertRaises(DjangoValidationError) as ctx:
            resend_company_invitation(
                invitation_id="inv-123",
                empresa_id=1,
                solicitante=self.user
            )
        self.assertIn("Debe esperar al menos 60 segundos entre reenvíos.", str(ctx.exception))

    # 10.5 Tolerant system notification failure in acceptance
    @patch('apps.authorization.services.invitation_accept_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.invitation_accept_service.InvitacionUsuario.objects.using')
    @patch('apps.authorization.services.invitation_accept_service.Usuario.objects.using')
    @patch('apps.authorization.services.invitation_accept_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.invitation_accept_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.invitation_accept_service.UsuarioEmpresa.save')
    @patch('apps.authorization.services.invitation_accept_service.UsuarioEmpresaRol.save')
    @patch('apps.authorization.services.invitation_accept_service.RolHistorial.save')
    @patch('apps.authorization.services.invitation_accept_service.Notificacion.save')
    @patch('apps.authorization.services.invitation_accept_service.AuditService.record_event')
    def test_accept_invitation_notification_fail_tolerated(
        self, mock_audit, mock_notif_save, mock_historial, mock_uer_save, mock_uep_save,
        mock_uer_using, mock_uep_using, mock_user_using, mock_inv_using, mock_atomic
    ):
        from apps.authorization.services.invitation_accept_service import accept_company_invitation
        from datetime import timedelta
        
        # Mock invitation
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'newuser@example.com'
        mock_inv.fecha_expiracion = timezone.now() + timedelta(hours=24)
        mock_inv.rol = Rol(codigo="EDITOR", nombre="Editor")
        mock_inv.empresa = self.company
        mock_inv.invitado_por = self.user
        mock_inv_using.return_value.select_for_update.return_value.get.return_value = mock_inv
        
        # User is new
        mock_user_using.return_value.filter.return_value.first.return_value = None
        
        # Mock UsuarioEmpresa and UsuarioEmpresaRol querysets to return no existing relationship
        mock_uep_using.return_value.filter.return_value.exists.return_value = False
        mock_uep_using.return_value.filter.return_value.first.return_value = None
        mock_uer_using.return_value.filter.return_value.first.return_value = None
        
        # Notification throws an error on save
        mock_notif_save.side_effect = Exception("Transient DB Notification failure")
        
        with patch('apps.accounts.models.usuario.Usuario.save') as mock_user_save, \
             patch('apps.accounts.models.perfil.Perfil.save') as mock_profile_save:
            # Invitation should STILL succeed because notification failure is caught
            res = accept_company_invitation(
                plain_token="token-abc",
                password="strongpassword123",
                nombres="New",
                apellidos="User"
            )
            self.assertIsNotNone(res)
            mock_user_save.assert_called_once()
            mock_profile_save.assert_called_once()
            mock_notif_save.assert_called_once()

    # 10.6 Last active administrator protection logic
    @patch('apps.authorization.services.member_suspend_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.member_suspend_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.member_suspend_service.UsuarioEmpresaRol.objects.using')
    def test_suspend_last_admin_blocked(self, mock_uer_using, mock_uep_using, mock_atomic):
        from apps.authorization.services.member_suspend_service import suspend_company_member
        
        mock_uep = MagicMock(spec=UsuarioEmpresa)
        mock_uep.id = 15
        mock_uep.estado = 'ACTIVO'
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = mock_uep
        
        # Mock roles_asignados filter returning true (is admin)
        mock_uep.roles_asignados.filter.return_value.filter.return_value.exists.return_value = True
        
        # Mock other_admins count returning empty (no other active admins)
        mock_other_admins_qs = MagicMock()
        mock_other_admins_qs.filter.return_value.exclude.return_value.exists.return_value = False
        mock_uer_using.return_value.select_for_update.return_value.filter.return_value = mock_other_admins_qs
        
        with self.assertRaises(DjangoValidationError) as ctx:
            suspend_company_member(
                uep_id=15,
                empresa_id=1,
                solicitante=self.user,
                motivo="Suspender"
            )
        self.assertIn("No se puede suspender al único administrador activo de la empresa.", str(ctx.exception))

