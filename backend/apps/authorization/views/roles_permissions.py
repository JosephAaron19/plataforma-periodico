from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.permiso import Permiso
from apps.authorization.permissions.drf_permissions import HasCompanyPermission, HasAnyCompanyPermission
from apps.authorization.selectors.role_management_selectors import (
    get_available_company_roles,
    get_member_roles
)
from apps.authorization.selectors.permission_management_selectors import (
    get_available_company_permissions
)
from apps.authorization.selectors.auth_selector import get_user_direct_permissions
from apps.authorization.services.role_assignment_service import assign_role_to_member
from apps.authorization.services.role_finalize_service import finalize_member_role
from apps.authorization.services.role_primary_service import set_member_primary_role
from apps.authorization.services.direct_permission_grant_service import grant_direct_permission
from apps.authorization.services.direct_permission_revoke_service import revoke_direct_permission
from apps.authorization.services.direct_permission_remove_service import remove_direct_permission_exception
from apps.authorization.services.permission_service import calculate_effective_permissions

from apps.authorization.serializers.role_assignment import RolSerializer, UsuarioEmpresaRolSerializer, RoleAssignSerializer
from apps.authorization.serializers.role_primary import RoleFinalizeSerializer, RoleSetPrimarySerializer
from apps.authorization.serializers.direct_permission import PermisoSerializer, UsuarioEmpresaPermisoSerializer, DirectPermissionGrantSerializer
from apps.authorization.serializers.effective_permission import EffectivePermissionSerializer

class CompanyRoleListView(generics.ListAPIView):
    """
    GET: List all available company roles (excluding platform-level ones).
    """
    permission_classes = [HasAnyCompanyPermission]
    required_permissions = ['USUARIO_VER', 'ROL_GESTIONAR']
    serializer_class = RolSerializer

    def get_queryset(self):
        emp_id = self.kwargs.get('emp_id')
        qs = get_available_company_roles(emp_id)
        
        # Optional filters
        nombre = self.request.query_params.get('nombre')
        if nombre:
            qs = qs.filter(nombre__icontains=nombre)
        codigo = self.request.query_params.get('codigo')
        if codigo:
            qs = qs.filter(codigo__icontains=codigo)
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        return qs


class CompanyPermissionListView(generics.ListAPIView):
    """
    GET: List all available permissions in the company context (excluding platform-exclusive ones).
    """
    permission_classes = [HasAnyCompanyPermission]
    required_permissions = ['USUARIO_VER', 'ROL_GESTIONAR']
    serializer_class = PermisoSerializer

    def get_queryset(self):
        emp_id = self.kwargs.get('emp_id')
        qs = get_available_company_permissions(emp_id)
        
        # Optional filters
        modulo = self.request.query_params.get('modulo')
        if modulo:
            qs = qs.filter(modulo=modulo)
        accion = self.request.query_params.get('accion')
        if accion:
            qs = qs.filter(accion=accion)
        codigo = self.request.query_params.get('codigo')
        if codigo:
            qs = qs.filter(codigo__icontains=codigo)
        es_critico = self.request.query_params.get('es_critico')
        if es_critico is not None:
            is_crit = es_critico.lower() in ('true', '1', 'yes')
            qs = qs.filter(es_critico=is_crit)
        return qs


class MemberRoleListAssignView(generics.GenericAPIView):
    """
    GET: List all roles assigned to the member.
    POST: Assign a new company role to the member.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [HasCompanyPermission()]
        return [HasAnyCompanyPermission()]

    required_permission = 'ROL_GESTIONAR'  # For POST
    required_permissions = ['USUARIO_VER', 'ROL_GESTIONAR']  # For GET

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoleAssignSerializer
        return UsuarioEmpresaRolSerializer

    def get(self, request, emp_id, uep_id):
        # Validate member exists and belongs to the company to prevent IDOR
        try:
            UsuarioEmpresa.objects.using('periodico_db').get(id=uep_id, empresa_id=emp_id)
        except UsuarioEmpresa.DoesNotExist:
            return Response({"detail": "El miembro especificado no existe o no pertenece a la empresa."}, status=status.HTTP_404_NOT_FOUND)

        qs = get_member_roles(uep_id, emp_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, emp_id, uep_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            uer = assign_role_to_member(
                uep_id=uep_id,
                emp_id=emp_id,
                role_code=serializer.validated_data['role_code'],
                is_primary=serializer.validated_data.get('is_primary', False),
                start_date=serializer.validated_data.get('start_date'),
                end_date=serializer.validated_data.get('end_date'),
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        response_serializer = UsuarioEmpresaRolSerializer(uer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MemberRoleFinalizeView(generics.GenericAPIView):
    """
    POST: Finalize a member's role assignment.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'ROL_GESTIONAR'
    serializer_class = RoleFinalizeSerializer

    def post(self, request, emp_id, uep_id, assignment_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            uer = finalize_member_role(
                uep_id=uep_id,
                emp_id=emp_id,
                uer_id=assignment_id,
                solicitante=request.user,
                motivo=serializer.validated_data['motivo'],
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        response_serializer = UsuarioEmpresaRolSerializer(uer)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class MemberRoleSetPrimaryView(generics.GenericAPIView):
    """
    POST: Change a member's primary role.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'ROL_GESTIONAR'
    serializer_class = RoleSetPrimarySerializer

    def post(self, request, emp_id, uep_id, assignment_id):
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            uer = set_member_primary_role(
                uep_id=uep_id,
                emp_id=emp_id,
                uer_id=assignment_id,
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        response_serializer = UsuarioEmpresaRolSerializer(uer)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class MemberEffectivePermissionListView(generics.GenericAPIView):
    """
    GET: List all effective permissions for a company member.
    """
    permission_classes = [HasAnyCompanyPermission]
    required_permissions = ['USUARIO_VER', 'ROL_GESTIONAR']
    serializer_class = EffectivePermissionSerializer

    def get(self, request, emp_id, uep_id):
        # Validate member exists and belongs to the company to prevent IDOR
        try:
            uep = UsuarioEmpresa.objects.using('periodico_db').get(id=uep_id, empresa_id=emp_id)
        except UsuarioEmpresa.DoesNotExist:
            return Response({"detail": "El miembro especificado no existe o no pertenece a la empresa."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Calculate effective permissions codes using service
        effective_codes = calculate_effective_permissions(uep.usuario_id, emp_id)

        # 2. Retrieve corresponding Permiso objects to present names
        active_permissions = Permiso.objects.using('periodico_db').filter(
            estado='ACTIVO',
            codigo__in=effective_codes
        )

        # 3. Determine origin for each permission (concession vs inherited role)
        direct_permissions = get_user_direct_permissions(uep.usuario_id, emp_id)
        direct_concedes = {
            dp.permiso.codigo for dp in direct_permissions
            if dp.tipo == 'CONCEDER'
        }
        direct_revokes = {
            dp.permiso.codigo for dp in direct_permissions
            if dp.tipo == 'REVOCAR'
        }

        data = []
        for perm in active_permissions:
            origen = 'CONCESION_DIRECTA' if perm.codigo in direct_concedes else 'ROL'
            data.append({
                'permission_code': perm.codigo,
                'nombre': perm.nombre,
                'granted': True,
                'origin': origen
            })

        # 4. Include explicit revocations as REVOCACION_DIRECTA
        if direct_revokes:
            revoked_permissions = Permiso.objects.using('periodico_db').filter(
                estado='ACTIVO',
                codigo__in=direct_revokes
            )
            for perm in revoked_permissions:
                data.append({
                    'permission_code': perm.codigo,
                    'nombre': perm.nombre,
                    'granted': False,
                    'origin': 'REVOCACION_DIRECTA'
                })

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MemberPermissionGrantView(generics.GenericAPIView):
    """
    POST: Concede a direct permission exception to a member.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'ROL_GESTIONAR'
    serializer_class = DirectPermissionGrantSerializer

    def post(self, request, emp_id, uep_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            uepr = grant_direct_permission(
                uep_id=uep_id,
                emp_id=emp_id,
                permission_code=serializer.validated_data['permission_code'],
                motivo=serializer.validated_data['reason'],
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        response_serializer = UsuarioEmpresaPermisoSerializer(uepr)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MemberPermissionRevokeView(generics.GenericAPIView):
    """
    POST: Revokes a direct permission exception from a member.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'ROL_GESTIONAR'
    serializer_class = DirectPermissionGrantSerializer

    def post(self, request, emp_id, uep_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            uepr = revoke_direct_permission(
                uep_id=uep_id,
                emp_id=emp_id,
                permission_code=serializer.validated_data['permission_code'],
                motivo=serializer.validated_data['reason'],
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        response_serializer = UsuarioEmpresaPermisoSerializer(uepr)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MemberPermissionRemoveExceptionView(generics.GenericAPIView):
    """
    DELETE: Retracts (disables) a direct permission exception from a member.
    """
    permission_classes = [HasCompanyPermission]
    required_permission = 'ROL_GESTIONAR'

    def delete(self, request, emp_id, uep_id, permission_code):
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

        try:
            uepr = remove_direct_permission_exception(
                uep_id=uep_id,
                emp_id=emp_id,
                permission_code=permission_code,
                solicitante=request.user,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        response_serializer = UsuarioEmpresaPermisoSerializer(uepr)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
