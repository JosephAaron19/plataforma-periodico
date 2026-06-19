from rest_framework import serializers
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa

class CompanyCreateSerializer(serializers.ModelSerializer):
    administrator_user_id = serializers.IntegerField(
        required=True,
        help_text="ID del usuario que actuará como administrador de la empresa."
    )

    class Meta:
        model = Empresa
        fields = [
            'ruc',
            'razon_social',
            'nombre_comercial',
            'slug',
            'descripcion',
            'correo',
            'telefono',
            'direccion',
            'sitio_web',
            'administrator_user_id'
        ]

    def validate_ruc(self, value):
        if not value or len(value) != 11 or not value.isdigit():
            raise serializers.ValidationError("El RUC debe ser una cadena numérica de exactamente 11 dígitos.")
        return value

    def validate_administrator_user_id(self, value):
        try:
            admin_user = Usuario.objects.using('periodico_db').get(id=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError("El usuario administrador seleccionado no existe.")
        
        if admin_user.eliminado or admin_user.estado != 'ACTIVO':
            raise serializers.ValidationError("El usuario administrador seleccionado no está activo.")
        if not admin_user.correo_verificado:
            raise serializers.ValidationError("El usuario administrador seleccionado no tiene el correo verificado.")
        if admin_user.bloqueado_hasta and admin_user.bloqueado_hasta > timezone.now():
            raise serializers.ValidationError("El usuario administrador seleccionado tiene un bloqueo vigente.")
            
        return value
