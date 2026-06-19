from rest_framework import serializers
from apps.authorization.models.permiso import Permiso
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.serializers.member import UserSimpleSerializer

class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'modulo', 'accion', 'es_critico', 'estado']

class UsuarioEmpresaPermisoSerializer(serializers.ModelSerializer):
    permiso = PermisoSerializer(read_only=True)
    asignado_por = UserSimpleSerializer(read_only=True)

    class Meta:
        model = UsuarioEmpresaPermiso
        fields = [
            'id',
            'usuario_empresa',
            'permiso',
            'tipo',
            'motivo',
            'asignado_por',
            'fecha_inicio',
            'fecha_fin',
            'estado'
        ]

class DirectPermissionGrantSerializer(serializers.Serializer):
    permission_code = serializers.CharField(max_length=100, required=True)
    reason = serializers.CharField(max_length=500, required=True)
