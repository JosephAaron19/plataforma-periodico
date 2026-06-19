from django.test import SimpleTestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate
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
from apps.authorization.models.invitacion_usuario import InvitacionUsuario
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol import Rol
from apps.authorization.models.rol_historial import RolHistorial

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

        # Patch check_user_limit to prevent database queries during SimpleTestCase
        for m in [
            'apps.authorization.services.invitation_create_service',
            'apps.authorization.services.invitation_accept_service',
            'apps.authorization.services.member_reactivate_service',
        ]:
            p_cul = patch(f'{m}.check_user_limit', return_value={"allowed": True, "limit": 10, "used": 1})
            self.patchers.append(p_cul)
            p_cul.start()

        # Patch Empresa.objects.using to prevent DB queries in SimpleTestCase
        for m in [
            'apps.authorization.services.invitation_accept_service',
            'apps.authorization.services.member_reactivate_service',
        ]:
            p_emp = patch(f'{m}.Empresa.objects.using')
            self.patchers.append(p_emp)
            mock_using = p_emp.start()
            mock_using.return_value.select_for_update.return_value.get.return_value = self.company

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

    # 10.5 Tolerant system notification failure in acceptance (using on_commit)
    @patch('apps.authorization.services.invitation_accept_service.transaction.on_commit')
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
        mock_uer_using, mock_uep_using, mock_user_using, mock_inv_using, mock_atomic, mock_on_commit
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
        
        # Simulate immediate execution of on_commit callback
        mock_on_commit.side_effect = lambda func, using=None: func()
        
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
            # Verify on_commit receives using="periodico_db"
            mock_on_commit.assert_called_once_with(ANY, using='periodico_db')
            # Verify the notification is saved with using="periodico_db"
            mock_notif_save.assert_called_once_with(using='periodico_db')

    # 10.5.2 Rollback does not fire notification
    @patch('apps.authorization.services.invitation_accept_service.transaction.on_commit')
    @patch('apps.authorization.services.invitation_accept_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.invitation_accept_service.InvitacionUsuario.objects.using')
    def test_accept_invitation_rollback_does_not_fire_notification(
        self, mock_inv_using, mock_atomic, mock_on_commit
    ):
        from apps.authorization.services.invitation_accept_service import accept_company_invitation
        
        # Mock expired invitation to force early failure/rollback scenario
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.fecha_expiracion = timezone.now() - timedelta(hours=1) # Expired
        mock_inv_using.return_value.select_for_update.return_value.get.return_value = mock_inv
        
        with self.assertRaises(DjangoValidationError):
            accept_company_invitation(plain_token="token-abc")
            
        # The transaction fails/rolls back before registering on_commit, so it must not be called
        mock_on_commit.assert_not_called()

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

    # 10.7 Conservative member reactivation logic
    @patch('apps.authorization.services.member_reactivate_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.authorization.services.member_reactivate_service.UsuarioEmpresa.objects.using')
    @patch('apps.authorization.services.member_reactivate_service.UsuarioEmpresaRol.objects.using')
    @patch('apps.authorization.services.member_reactivate_service.RolHistorial.objects.using')
    @patch('apps.authorization.services.member_reactivate_service.RolHistorial.save')
    def test_reactivate_member_conservative_roles(
        self, mock_historial_save, mock_historial_using, mock_uer_using, mock_uep_using, mock_atomic
    ):
        from apps.authorization.services.member_reactivate_service import reactivate_company_member
        
        mock_uep = UsuarioEmpresa(
            id=12,
            estado='SUSPENDIDO',
            empresa=self.company,
            usuario=self.user
        )
        mock_uep.save = MagicMock()
        mock_uep_using.return_value.select_for_update.return_value.get.return_value = mock_uep
        
        # Roles in history that were suspended specifically due to member suspension
        mock_historial_using.return_value.filter.return_value.values_list.return_value = [101, 102]
        
        # Two roles exist in database for this member:
        # 1. Editor (role_id=101, es_principal=True, estado='SUSPENDIDO') -> Should be reactivated
        # 2. Viewer (role_id=102, es_principal=False, estado='SUSPENDIDO') -> Should remain suspended (conservative policy)
        role_editor = UsuarioEmpresaRol(
            id=1,
            usuario_empresa=mock_uep,
            rol=Rol(codigo="EDITOR", nombre="Editor"),
            es_principal=True,
            estado='SUSPENDIDO'
        )
        role_editor.save = MagicMock()
        
        # Configure queryset filter
        mock_qs = MagicMock()
        mock_qs.filter.return_value.first.return_value = role_editor
        mock_uer_using.return_value.filter.return_value = mock_qs
        
        res = reactivate_company_member(
            uep_id=12,
            empresa_id=1,
            solicitante=self.user
        )
        
        self.assertEqual(res.estado, 'ACTIVO')
        role_editor.save.assert_called_once()
        self.assertEqual(role_editor.estado, 'ACTIVO')
        mock_historial_save.assert_called_once()

    # 10.8 Rate limit verification policy (strictly no audit table lookup dependencies)
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    def test_rate_limit_policy_no_audit(self, mock_inv_using):
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        # Mock invitation sent 70 seconds ago (cooldown > 60s)
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'test@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
        mock_inv_using.return_value.get.return_value = mock_inv
        
        # We patch send_company_invitation_email_task to avoid celery queueing
        with patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url') as mock_redis_from_url, \
             patch('apps.authorization.services.invitation_resend_service.send_company_invitation_email_task'), \
             patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=dummy_atomic), \
             patch('apps.authorization.services.invitation_resend_service.transaction.on_commit', side_effect=lambda f, using=None: None), \
             patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):
            mock_redis_client = MagicMock()
            mock_redis_from_url.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            mock_redis_client.eval.return_value = 1
            
            res = resend_company_invitation(
                invitation_id="inv-123",
                empresa_id=1,
                solicitante=self.user
            )
            self.assertEqual(res.estado, 'REENVIADA')

    # 10.9 Redis rate limit success and error scenarios
    @patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url')
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    def test_resend_invitation_redis_flow(self, mock_inv_using, mock_redis_from_url):
        from apps.authorization.services.invitation_resend_service import (
            resend_company_invitation,
            RateLimitExceededException,
            RedisUnavailableException
        )
        
        # Mock Redis Client and connection ping
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        
        # Mock invitation
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'testlimit@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70) # cooldown passed
        mock_inv_using.return_value.get.return_value = mock_inv

        # Helper mocks
        with patch('apps.authorization.services.invitation_resend_service.send_company_invitation_email_task'), \
             patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=dummy_atomic), \
             patch('apps.authorization.services.invitation_resend_service.transaction.on_commit', side_effect=lambda f, using=None: None), \
             patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):

            # Scenario A: First resend (eval returns 1)
            mock_redis_client.eval.return_value = 1
            mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
            res = resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            self.assertEqual(res.estado, 'REENVIADA')
            mock_redis_client.eval.assert_called_once()
            
            # Verify the key has f"invitation:resend:1:inv-123:" and email hash without raw email
            redis_call_key = mock_redis_client.eval.call_args[0][2]
            self.assertIn("invitation:resend:1:inv-123:", redis_call_key)
            self.assertNotIn("testlimit@example.com", redis_call_key)
            
            # Scenario B: Fifth resend (eval returns 5, which is permitted)
            mock_redis_client.eval.reset_mock()
            mock_redis_client.eval.return_value = 5
            mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
            res = resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            self.assertEqual(res.estado, 'REENVIADA')
            mock_redis_client.eval.assert_called_once()
            
            # Scenario C: Sixth resend (eval returns 0, limit exceeded)
            mock_redis_client.eval.reset_mock()
            mock_redis_client.eval.return_value = 0
            mock_redis_client.ttl.return_value = 50000
            mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
            
            with self.assertRaises(RateLimitExceededException) as ctx:
                resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            self.assertEqual(ctx.exception.retry_after, 50000)
            
            # Scenario D: Redis unavailable (ping fails)
            mock_redis_client.ping.side_effect = Exception("Redis down")
            mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
            with self.assertRaises(RedisUnavailableException):
                resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
                
            # Reset side effect
            mock_redis_client.ping.side_effect = None

    # 10.10 Postgres failure decrements/releases Redis reservation using Lua script
    @patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url')
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    def test_resend_invitation_postgres_failure_releases_redis(self, mock_inv_using, mock_redis_from_url):
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.eval.return_value = 1 # Slot successfully reserved in Redis
        
        # Mock invitation
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'test@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
        mock_inv_using.return_value.get.return_value = mock_inv
        
        # Simulate Postgres exception inside transaction.atomic (e.g. database connection timeout)
        def postgres_fail_save(*args, **kwargs):
            raise Exception("Postgres connection timeout")
        mock_inv.save.side_effect = postgres_fail_save
        
        with patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=postgres_fail_save), \
             patch('apps.authorization.services.invitation_resend_service.transaction.on_commit', side_effect=lambda f, using=None: f()):
             
            with self.assertRaises(Exception) as ctx:
                resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            self.assertIn("Postgres connection timeout", str(ctx.exception))
            
            # Redis eval must be called twice: once to increment, and once to run the LUA_RELEASE_SCRIPT
            self.assertEqual(mock_redis_client.eval.call_count, 2)
            second_call_script = mock_redis_client.eval.call_args_list[1][0][0]
            self.assertIn("decr", second_call_script)

    # 10.11 Celery failure after commit does NOT release Redis reservation
    @patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url')
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    def test_resend_invitation_celery_failure_does_not_release_redis(self, mock_inv_using, mock_redis_from_url):
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.eval.return_value = 1
        
        # Mock invitation
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'test@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
        mock_inv_using.return_value.get.return_value = mock_inv
        
        callbacks = []
        def store_callback(func, using=None):
            callbacks.append(func)
            
        with patch('apps.authorization.services.invitation_resend_service.send_company_invitation_email_task.delay', side_effect=Exception("Celery Broker Offline")), \
             patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=dummy_atomic), \
             patch('apps.authorization.services.invitation_resend_service.transaction.on_commit', side_effect=store_callback), \
             patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):
             
            res = resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            self.assertEqual(res.estado, 'REENVIADA')
            
            # Now, simulate Django running the on_commit callbacks post-commit
            self.assertEqual(len(callbacks), 1)
            with self.assertRaises(Exception) as ctx:
                callbacks[0]()
            self.assertIn("Celery Broker Offline", str(ctx.exception))
            
            # The reservation in Redis must NOT be released, since the invitation was already committed to DB
            mock_redis_client.decr.assert_not_called()

    # 10.12 View handles custom rate limit exceptions returning HTTP 503 and 429
    @patch('apps.authorization.views.invitations.HasCompanyPermission.has_permission', return_value=True)
    @patch('apps.authorization.views.invitations.resend_company_invitation')
    def test_resend_invitation_views_http_responses(self, mock_resend, mock_has_perm):
        from apps.authorization.services.invitation_resend_service import (
            RedisUnavailableException,
            RateLimitExceededException
        )
        inv_id = str(uuid.uuid4())
        
        # Scenario A: 503 Service Unavailable when Redis is down
        mock_resend.side_effect = RedisUnavailableException("Redis is down")
        request = self.factory.post(f'/api/v1/companies/1/invitations/{inv_id}/resend/', {})
        force_authenticate(request, user=self.user)
        view = CompanyInvitationResendView.as_view()
        response = view(request, emp_id=1, invitation_id=inv_id)
        
        self.assertEqual(response.status_code, 503)
        self.assertIn("Servicio de control de frecuencia", response.data['detail'])
        
        # Scenario B: 429 Too Many Requests when limit is reached
        mock_resend.side_effect = RateLimitExceededException(retry_after=12345)
        response = view(request, emp_id=1, invitation_id=inv_id)
        
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers.get("Retry-After"), "12345")
        self.assertIn("límite máximo de reenvíos", response.data['detail'])

    # 10.13 Redis limit and 24-hour TTL arguments verification
    @patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url')
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    def test_resend_invitation_redis_ttl_and_limit(self, mock_inv_using, mock_redis_from_url):
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.eval.return_value = 1
        
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'ttltest@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
        mock_inv_using.return_value.get.return_value = mock_inv
        
        with patch('apps.authorization.services.invitation_resend_service.send_company_invitation_email_task'), \
             patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=dummy_atomic), \
             patch('apps.authorization.services.invitation_resend_service.transaction.on_commit', side_effect=lambda f, using=None: None), \
             patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):
             
            resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            
            # Assert eval was called with limit=5 and TTL=86400 (24 hours)
            mock_redis_client.eval.assert_called_once()
            args, kwargs = mock_redis_client.eval.call_args
            self.assertEqual(args[1], 1)
            self.assertEqual(args[3], 5)
            self.assertEqual(args[4], 86400)

    # 10.14 TTL no reiniciado simulation
    def test_lua_script_simulation_no_ttl_restart(self):
        # Simulate the Lua script logic in python to verify that TTL is not restarted on subsequent calls
        redis_store = {}
        redis_ttl = {}
        
        def run_lua_sim(key, limit, ttl):
            current = redis_store.get(key)
            if current is not None:
                if current >= limit:
                    return 0
                else:
                    redis_store[key] = current + 1
                    return redis_store[key]
            else:
                redis_store[key] = 1
                redis_ttl[key] = ttl
                return 1
        
        # First call (new key)
        res1 = run_lua_sim("key1", 5, 86400)
        self.assertEqual(res1, 1)
        self.assertEqual(redis_ttl["key1"], 86400)
        
        # Second call (existing key) - simulated passage of time, TTL is now 50000
        redis_ttl["key1"] = 50000
        res2 = run_lua_sim("key1", 5, 86400)
        self.assertEqual(res2, 2)
        # TTL should not be restarted, remaining at 50000
        self.assertEqual(redis_ttl["key1"], 50000)

    # 10.15 Concurrencia simulada safety
    def test_resend_invitation_concurrency_safe_lua(self):
        """
        Verify that the rate limiter performs a single atomic script evaluation
        instead of vulnerability-prone GET/SET operations.
        """
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        with patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url') as mock_redis_from_url:
            mock_redis_client = MagicMock()
            mock_redis_from_url.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            mock_inv = MagicMock(spec=InvitacionUsuario)
            mock_inv.estado = 'PENDIENTE'
            mock_inv.correo = 'race@example.com'
            mock_inv.fecha_aceptacion = None
            mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
            
            with patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using') as mock_inv_using, \
                 patch('apps.authorization.services.invitation_resend_service.send_company_invitation_email_task'), \
                 patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=dummy_atomic), \
                 patch('apps.authorization.services.invitation_resend_service.transaction.on_commit'), \
                 patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):
                 
                mock_inv_using.return_value.get.return_value = mock_inv
                mock_redis_client.eval.return_value = 1
                
                resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
                
                mock_redis_client.eval.assert_called_once()
                mock_redis_client.get.assert_not_called()
                mock_redis_client.set.assert_not_called()

    # 10.16 No token regeneration when limit is exhausted
    @patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url')
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    @patch('apps.authorization.services.invitation_resend_service.secrets.token_urlsafe')
    def test_resend_invitation_no_token_regeneration_when_limit_exhausted(
        self, mock_token_urlsafe, mock_inv_using, mock_redis_from_url
    ):
        from apps.authorization.services.invitation_resend_service import (
            resend_company_invitation,
            RateLimitExceededException
        )
        
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.eval.return_value = 0  # Limit reached
        mock_redis_client.ttl.return_value = 100
        
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'limit@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
        mock_inv_using.return_value.get.return_value = mock_inv
        
        with patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):
            with self.assertRaises(RateLimitExceededException):
                resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
                
            mock_token_urlsafe.assert_not_called()
            mock_inv.save.assert_not_called()

    # 10.17 on_commit uses periodico_db for resending
    @patch('apps.authorization.services.invitation_resend_service.redis.Redis.from_url')
    @patch('apps.authorization.services.invitation_resend_service.InvitacionUsuario.objects.using')
    @patch('apps.authorization.services.invitation_resend_service.transaction.on_commit')
    def test_resend_invitation_on_commit_uses_correct_db(self, mock_on_commit, mock_inv_using, mock_redis_from_url):
        from apps.authorization.services.invitation_resend_service import resend_company_invitation
        
        mock_redis_client = MagicMock()
        mock_redis_from_url.return_value = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.eval.return_value = 1
        
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'dbtest@example.com'
        mock_inv.fecha_aceptacion = None
        mock_inv.fecha_envio = timezone.now() - timedelta(seconds=70)
        mock_inv_using.return_value.get.return_value = mock_inv
        
        with patch('apps.authorization.services.invitation_resend_service.send_company_invitation_email_task'), \
             patch('apps.authorization.services.invitation_resend_service.transaction.atomic', side_effect=dummy_atomic), \
             patch('apps.authorization.services.invitation_resend_service.AuditService.record_event'):
             
            resend_company_invitation(invitation_id="inv-123", empresa_id=1, solicitante=self.user)
            mock_on_commit.assert_called_once_with(ANY, using='periodico_db')

    # 10.18 Accept invitation system notification registered on_commit and not executed before
    @patch('apps.authorization.services.invitation_accept_service.transaction.on_commit')
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
    def test_accept_invitation_on_commit_not_executed_before_commit(
        self, mock_audit, mock_notif_save, mock_historial, mock_uer_save, mock_uep_save,
        mock_uer_using, mock_uep_using, mock_user_using, mock_inv_using, mock_atomic, mock_on_commit
    ):
        from apps.authorization.services.invitation_accept_service import accept_company_invitation
        
        mock_inv = MagicMock(spec=InvitacionUsuario)
        mock_inv.estado = 'PENDIENTE'
        mock_inv.correo = 'newuser@example.com'
        mock_inv.fecha_expiracion = timezone.now() + timedelta(hours=24)
        mock_inv.rol = Rol(codigo="EDITOR", nombre="Editor")
        mock_inv.empresa = self.company
        mock_inv.invitado_por = self.user
        mock_inv_using.return_value.select_for_update.return_value.get.return_value = mock_inv
        
        mock_user_using.return_value.filter.return_value.first.return_value = None
        mock_uep_using.return_value.filter.return_value.exists.return_value = False
        mock_uep_using.return_value.filter.return_value.first.return_value = None
        mock_uer_using.return_value.filter.return_value.first.return_value = None
        
        registered_callbacks = []
        mock_on_commit.side_effect = lambda func, using=None: registered_callbacks.append(func)
        
        with patch('apps.accounts.models.usuario.Usuario.save'), \
             patch('apps.accounts.models.perfil.Perfil.save'):
             
            accept_company_invitation(
                plain_token="token-abc",
                password="strongpassword123",
                nombres="New",
                apellidos="User"
            )
            
            self.assertEqual(len(registered_callbacks), 1)
            mock_notif_save.assert_not_called()

    # 10.19 LUA_RELEASE_SCRIPT logic simulation
    def test_lua_release_script_simulation(self):
        # Simulate the Lua release script logic in python
        # LUA_RELEASE_SCRIPT checks that the key exists, that the counter is > 0,
        # and decrements only in that case, conserving the TTL and not creating a new key.
        
        def run_release_sim(redis_store, redis_ttl, key):
            current = redis_store.get(key)
            if current is not None:
                val = current
                if val > 0:
                    redis_store[key] = val - 1
                    return redis_store[key]
                else:
                    return 0
            else:
                return 0

        # Case A: Key exists and is > 0 (e.g. 3) -> decrements to 2, TTL preserved
        redis_store = {"key1": 3}
        redis_ttl = {"key1": 50000}
        res = run_release_sim(redis_store, redis_ttl, "key1")
        self.assertEqual(res, 2)
        self.assertEqual(redis_store["key1"], 2)
        self.assertEqual(redis_ttl["key1"], 50000)

        # Case B: Key exists and is already 0 -> does not decrement, counter never negative
        redis_store = {"key1": 0}
        redis_ttl = {"key1": 50000}
        res = run_release_sim(redis_store, redis_ttl, "key1")
        self.assertEqual(res, 0)
        self.assertEqual(redis_store["key1"], 0)
        self.assertEqual(redis_ttl["key1"], 50000)

        # Case C: Key has already expired (doesn't exist) -> does not recreate key, absence of new key
        redis_store = {}
        redis_ttl = {}
        res = run_release_sim(redis_store, redis_ttl, "key1")
        self.assertEqual(res, 0)
        self.assertNotIn("key1", redis_store)
        self.assertNotIn("key1", redis_ttl)

