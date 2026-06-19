from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.authorization.selectors.invitation_selectors import get_company_invitations_queryset
from apps.authorization.services.invitation_create_service import create_company_invitation
from apps.authorization.services.invitation_resend_service import resend_company_invitation
from apps.authorization.services.invitation_revoke_service import revoke_company_invitation
from apps.authorization.services.invitation_accept_service import accept_company_invitation

from apps.authorization.serializers.invitation_create import CompanyInvitationCreateSerializer
from apps.authorization.serializers.invitation_accept import InvitationAcceptSerializer
from apps.authorization.serializers.invitation_list import CompanyInvitationSerializer
from apps.authorization.serializers.member import CompanyMemberSerializer

from apps.authorization.permissions.drf_permissions import HasCompanyAccess, HasCompanyPermission

class CompanyInvitationListCreateView(generics.ListCreateAPIView):
    """
    GET: List all invitations for a given company.
    POST: Create and send a new user invitation for the company.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CompanyInvitationCreateSerializer
        return CompanyInvitationSerializer

    def get_queryset(self):
        emp_id = self.kwargs.get('emp_id')
        return get_company_invitations_queryset(emp_id).order_by('-fecha_envio')

    def create(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            invitation = create_company_invitation(
                empresa_id=emp_id,
                email=serializer.validated_data['email'],
                role_code=serializer.validated_data['role_code'],
                invitado_por=request.user,
                mensaje=serializer.validated_data.get('mensaje'),
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
        
        response_serializer = CompanyInvitationSerializer(invitation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CompanyInvitationResendView(generics.GenericAPIView):
    """
    POST: Resends a pending/resent company invitation with rate limiting.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = CompanyInvitationSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        invitation_id = self.kwargs.get('invitation_id')
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        from apps.authorization.services.invitation_resend_service import (
            RedisUnavailableException,
            RateLimitExceededException
        )
        
        try:
            invitation = resend_company_invitation(
                invitation_id=invitation_id,
                empresa_id=emp_id,
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except RedisUnavailableException as e:
            return Response(
                {"detail": "Servicio de control de frecuencia temporalmente no disponible. Inténtelo más tarde."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except RateLimitExceededException as e:
            headers = {}
            if e.retry_after is not None:
                headers["Retry-After"] = str(e.retry_after)
            return Response(
                {"detail": "Has alcanzado el límite máximo de reenvíos para esta invitación hoy. Inténtelo más tarde."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=headers
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
            
        response_serializer = CompanyInvitationSerializer(invitation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CompanyInvitationRevokeView(generics.GenericAPIView):
    """
    POST: Revokes a pending/resent company invitation.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'USUARIO_GESTIONAR'
    serializer_class = CompanyInvitationSerializer

    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        invitation_id = self.kwargs.get('invitation_id')
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            invitation = revoke_company_invitation(
                invitation_id=invitation_id,
                empresa_id=emp_id,
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
            
        response_serializer = CompanyInvitationSerializer(invitation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class InvitationAcceptView(generics.GenericAPIView):
    """
    POST: Accept a company invitation using a plain token.
    Public endpoint. Existing users must be logged in with matching emails.
    """
    permission_classes = [AllowAny]
    serializer_class = InvitationAcceptSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        logged_in_user = request.user if request.user and request.user.is_authenticated else None
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            member_relation = accept_company_invitation(
                plain_token=serializer.validated_data['token'],
                password=serializer.validated_data.get('password'),
                nombres=serializer.validated_data.get('nombres'),
                apellidos=serializer.validated_data.get('apellidos'),
                logged_in_user=logged_in_user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)
        
        response_serializer = CompanyMemberSerializer(member_relation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
