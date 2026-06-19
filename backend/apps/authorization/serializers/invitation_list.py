from rest_framework import serializers
from apps.authorization.models.invitacion_usuario import InvitacionUsuario

class RoleSimpleSerializer(serializers.Serializer):
    codigo = serializers.CharField(read_only=True)
    nombre = serializers.CharField(read_only=True)

class UserSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    usr_correo = serializers.EmailField(read_only=True)
    nombres = serializers.CharField(read_only=True)
    apellidos = serializers.CharField(read_only=True)

class CompanyInvitationSerializer(serializers.ModelSerializer):
    rol = RoleSimpleSerializer(read_only=True)
    invitado_por = UserSimpleSerializer(read_only=True)
    usuario = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = InvitacionUsuario
        fields = [
            'id',
            'correo',
            'estado',
            'mensaje',
            'fecha_envio',
            'fecha_expiracion',
            'fecha_aceptacion',
            'rol',
            'invitado_por',
            'usuario'
        ]
