from django.test import SimpleTestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch, MagicMock
import uuid

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
