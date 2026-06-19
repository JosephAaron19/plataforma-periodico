from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound

from apps.authorization.selectors.member_selectors import get_company_members_queryset
from apps.authorization.services.member_suspend_service import suspend_company_member
from apps.authorization.services.member_reactivate_service import reactivate_company_member

from apps.authorization.serializers.member import CompanyMemberSerializer, MemberSuspendSerializer
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.permissions.drf_permissions import HasCompanyAccess, HasCompanyPermission

class CompanyMemberListView(generics.ListAPIView):
    """
    GET: List all active/suspended members of a given company.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_VER'
    serializer_class = CompanyMemberSerializer

    def get_queryset(self):
        emp_id = self.kwargs.get('emp_id')
        return get_company_members_queryset(emp_id).order_by('usuario__nombres')


class CompanyMemberDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a specific member in the company.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_VER'
    serializer_class = CompanyMemberSerializer

    def get_object(self):
        emp_id = self.kwargs.get('emp_id')
        uep_id = self.kwargs.get('uep_id')
        try:
            return get_company_members_queryset(emp_id).get(id=uep_id)
        except UsuarioEmpresa.DoesNotExist:
            raise NotFound("El miembro especificado no existe.")


class CompanyMemberSuspendView(generics.GenericAPIView):
    """
    POST: Suspends a company member relationship.
    Prevents leaving the company without an active administrator.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = MemberSuspendSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        uep_id = self.kwargs.get('uep_id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            member_relation = suspend_company_member(
                uep_id=uep_id,
                empresa_id=emp_id,
                solicitante=request.user,
                motivo=serializer.validated_data['motivo'],
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
            
        response_serializer = CompanyMemberSerializer(member_relation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CompanyMemberReactivateView(generics.GenericAPIView):
    """
    POST: Reactivates a suspended company member relationship.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = CompanyMemberSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        uep_id = self.kwargs.get('uep_id')
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            member_relation = reactivate_company_member(
                uep_id=uep_id,
                empresa_id=emp_id,
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
            
        response_serializer = CompanyMemberSerializer(member_relation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
