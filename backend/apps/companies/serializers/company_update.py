from rest_framework import serializers
from apps.companies.models.empresa import Empresa

class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            'razon_social',
            'nombre_comercial',
            'descripcion',
            'correo',
            'telefono',
            'direccion',
            'sitio_web'
        ]
