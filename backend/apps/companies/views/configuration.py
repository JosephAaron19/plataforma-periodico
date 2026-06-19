from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_configuracion import EmpresaConfiguracion
from apps.companies.serializers.company_configuration import CompanyConfigurationSerializer
from apps.companies.services.company_configuration_service import update_company_configuration
from apps.authorization.permissions.drf_permissions import HasCompanyAccess, HasCompanyPermission

class CompanyConfigurationView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve company configurations.
    PATCH: Update company configurations (Requires 'EMPRESA_CONFIGURACION_EDITAR').
    """
    serializer_class = CompanyConfigurationSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT']:
            self.required_permission = 'EMPRESA_CONFIGURACION_EDITAR'
            return [HasCompanyPermission()]
        return [HasCompanyAccess()]

    def get_object(self):
        emp_id = self.kwargs.get('emp_id')
        empresa = get_object_or_404(Empresa.objects.filter(eliminado=False), id=emp_id)
        try:
            return empresa.configuracion
        except EmpresaConfiguracion.DoesNotExist:
            config = EmpresaConfiguracion(empresa=empresa, estado='ACTIVA')
            config.save(using='periodico_db')
            return config

    def update(self, request, *args, **kwargs):
        config = self.get_object()
        serializer = self.get_serializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        updated_config = update_company_configuration(
            empresa=config.empresa,
            actualizado_por=request.user,
            config_data=serializer.validated_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        response_serializer = self.get_serializer(updated_config)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
