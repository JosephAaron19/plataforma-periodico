from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.companies.models.empresa import Empresa
from apps.companies.selectors.company_selectors import (
    get_all_companies_for_admin,
    get_authorized_companies_for_user
)
from apps.companies.services.company_create_service import create_company
from apps.companies.services.company_update_service import update_company
from apps.companies.serializers.company_create import CompanyCreateSerializer
from apps.companies.serializers.company_detail import CompanyDetailSerializer
from apps.companies.serializers.company_update import CompanyUpdateSerializer

from apps.authorization.permissions.drf_permissions import (
    IsAuthenticatedAndActive,
    HasCompanyAccess,
    HasCompanyPermission,
    IsPlatformSuperadmin
)
from apps.authorization.services.permission_service import is_platform_superadmin

class CompanyListCreateView(generics.ListCreateAPIView):
    """
    GET: List authorized companies for the user (or all if platform superadmin).
    POST: Create a new company (Platform Superadmin only).
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsPlatformSuperadmin()]
        return [IsAuthenticatedAndActive()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CompanyCreateSerializer
        return CompanyDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if is_platform_superadmin(user):
            return get_all_companies_for_admin()
        return get_authorized_companies_for_user(user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get IP and User-Agent for audit log
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        # Call transactional creation service
        company = create_company(
            ruc=serializer.validated_data['ruc'],
            razon_social=serializer.validated_data['razon_social'],
            nombre_comercial=serializer.validated_data['nombre_comercial'],
            slug=serializer.validated_data['slug'],
            creado_por=request.user,
            administrator_user_id=serializer.validated_data['administrator_user_id'],
            descripcion=serializer.validated_data.get('descripcion'),
            correo=serializer.validated_data.get('correo'),
            telefono=serializer.validated_data.get('telefono'),
            direccion=serializer.validated_data.get('direccion'),
            sitio_web=serializer.validated_data.get('sitio_web'),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Serialize response with detail serializer
        response_serializer = CompanyDetailSerializer(company)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CompanyDetailUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve company details (Requires active company access).
    PATCH/PUT: Update company general mutable details (Requires HasCompanyPermission: 'EMPRESA_EDITAR').
    """
    serializer_class = CompanyDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT']:
            self.required_permission = 'EMPRESA_EDITAR'
            return [HasCompanyPermission()]
        return [HasCompanyAccess()]

    def get_object(self):
        emp_id = self.kwargs.get('emp_id')
        queryset = Empresa.objects.filter(eliminado=False).select_related('configuracion', 'identidad')
        obj = get_object_or_404(queryset, id=emp_id)
        return obj

    def update(self, request, *args, **kwargs):
        # We enforce partial update (PATCH) and only use mutable serializer fields
        company = self.get_object()
        serializer = CompanyUpdateSerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Get IP and User-Agent
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        # Call update service
        updated_company = update_company(
            empresa=company,
            actualizado_por=request.user,
            razon_social=serializer.validated_data.get('razon_social'),
            nombre_comercial=serializer.validated_data.get('nombre_comercial'),
            descripcion=serializer.validated_data.get('descripcion'),
            correo=serializer.validated_data.get('correo'),
            telefono=serializer.validated_data.get('telefono'),
            direccion=serializer.validated_data.get('direccion'),
            sitio_web=serializer.validated_data.get('sitio_web'),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        response_serializer = CompanyDetailSerializer(updated_company)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
