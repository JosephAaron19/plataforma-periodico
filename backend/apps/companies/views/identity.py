from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_identidad import EmpresaIdentidad
from apps.companies.serializers.company_identity import CompanyIdentitySerializer
from apps.companies.services.company_identity_service import update_company_identity
from apps.authorization.permissions.drf_permissions import HasCompanyAccess, HasCompanyPermission

class CompanyIdentityView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve company visual identity details.
    PATCH: Update company visual identity details (Requires 'EMPRESA_IDENTIDAD_EDITAR').
    """
    serializer_class = CompanyIdentitySerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT']:
            self.required_permission = 'EMPRESA_IDENTIDAD_EDITAR'
            return [HasCompanyPermission()]
        return [HasCompanyAccess()]

    def get_object(self):
        emp_id = self.kwargs.get('emp_id')
        empresa = get_object_or_404(Empresa.objects.filter(eliminado=False), id=emp_id)
        try:
            return empresa.identidad
        except EmpresaIdentidad.DoesNotExist:
            identidad = EmpresaIdentidad(empresa=empresa, estado='BORRADOR')
            identidad.save(using='periodico_db')
            return identidad

    def update(self, request, *args, **kwargs):
        identidad = self.get_object()
        serializer = self.get_serializer(identidad, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        updated_identidad = update_company_identity(
            empresa=identidad.empresa,
            actualizado_por=request.user,
            nombre_publico=serializer.validated_data.get('nombre_publico'),
            descripcion_corta=serializer.validated_data.get('descripcion_corta'),
            descripcion_larga=serializer.validated_data.get('descripcion_larga'),
            logo_archivo_id=serializer.validated_data.get('logo_archivo_id'),
            logo_reducido_archivo_id=serializer.validated_data.get('logo_reducido_archivo_id'),
            favicon_archivo_id=serializer.validated_data.get('favicon_archivo_id'),
            portada_archivo_id=serializer.validated_data.get('portada_archivo_id'),
            color_primario=serializer.validated_data.get('color_primario'),
            color_secundario=serializer.validated_data.get('color_secundario'),
            color_acento=serializer.validated_data.get('color_acento'),
            tipografia=serializer.validated_data.get('tipografia'),
            sitio_web=serializer.validated_data.get('sitio_web'),
            facebook=serializer.validated_data.get('facebook'),
            instagram=serializer.validated_data.get('instagram'),
            tiktok=serializer.validated_data.get('tiktok'),
            youtube=serializer.validated_data.get('youtube'),
            whatsapp=serializer.validated_data.get('whatsapp'),
            correo_publico=serializer.validated_data.get('correo_publico'),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        response_serializer = self.get_serializer(updated_identidad)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
