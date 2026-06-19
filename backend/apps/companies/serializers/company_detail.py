from rest_framework import serializers
from apps.companies.models.empresa import Empresa
from apps.companies.serializers.company_identity import CompanyIdentitySerializer
from apps.companies.serializers.company_configuration import CompanyConfigurationSerializer

class CompanyDetailSerializer(serializers.ModelSerializer):
    identidad = CompanyIdentitySerializer(read_only=True)
    configuracion = CompanyConfigurationSerializer(read_only=True)
    active_plan = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = [
            'id',
            'ruc',
            'razon_social',
            'nombre_comercial',
            'slug',
            'descripcion',
            'correo',
            'telefono',
            'direccion',
            'sitio_web',
            'estado',
            'fecha_activacion',
            'fecha_suspension',
            'motivo_suspension',
            'fecha_creacion',
            'fecha_actualizacion',
            'identidad',
            'configuracion',
            'active_plan'
        ]

    def get_active_plan(self, obj):
        from apps.companies.selectors.company_selectors import get_company_active_plan
        active_ep = get_company_active_plan(obj.id)
        if active_ep:
            return {
                "plan_codigo": active_ep.plan.codigo,
                "plan_nombre": active_ep.plan.nombre,
                "fecha_inicio": active_ep.fecha_inicio,
                "fecha_fin": active_ep.fecha_fin,
                "precio_contratado": str(active_ep.precio_contratado) if active_ep.precio_contratado else None,
                "moneda": active_ep.moneda,
                "periodicidad": active_ep.periodicidad,
                "estado": active_ep.estado
            }
        return None
