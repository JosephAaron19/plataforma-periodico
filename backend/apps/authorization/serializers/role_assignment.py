from rest_framework import serializers
from apps.authorization.models.rol import Rol
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.serializers.member import UserSimpleSerializer

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'tipo', 'estado']

class UsuarioEmpresaRolSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    asignado_por = UserSimpleSerializer(read_only=True)

    class Meta:
        model = UsuarioEmpresaRol
        fields = [
            'id',
            'usuario_empresa',
            'rol',
            'es_principal',
            'asignado_por',
            'fecha_inicio',
            'fecha_fin',
            'estado'
        ]

class RoleAssignSerializer(serializers.Serializer):
    role_code = serializers.CharField(max_length=50, required=True)
    is_primary = serializers.BooleanField(default=False)
    start_date = serializers.DateTimeField(required=False, allow_null=True, default=None)
    end_date = serializers.DateTimeField(required=False, allow_null=True, default=None)
