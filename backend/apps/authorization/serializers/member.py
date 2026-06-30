from rest_framework import serializers
from apps.authorization.models.usuario_empresa import UsuarioEmpresa

class UserSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    usr_correo = serializers.EmailField(read_only=True)
    nombres = serializers.CharField(read_only=True)
    apellidos = serializers.CharField(read_only=True)

class CompanyMemberRoleSerializer(serializers.Serializer):
    rol_codigo = serializers.CharField(source='rol.codigo', read_only=True)
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    es_principal = serializers.BooleanField(read_only=True)
    estado = serializers.CharField(read_only=True)

class CompanyMemberSerializer(serializers.ModelSerializer):
    usuario = UserSimpleSerializer(read_only=True)
    asignado_por = UserSimpleSerializer(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = UsuarioEmpresa
        fields = [
            'id',
            'usuario',
            'es_principal',
            'fecha_asignacion',
            'fecha_finalizacion',
            'estado',
            'asignado_por',
            'motivo',
            'fecha_actualizacion',
            'roles'
        ]

    def get_roles(self, obj):
        # Filter roles physically active or suspended but mapped to this relation
        active_uer = obj.roles_asignados.filter(estado__in=['ACTIVO', 'SUSPENDIDO'])
        return CompanyMemberRoleSerializer(active_uer, many=True).data

class MemberSuspendSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        required=True,
        max_length=300,
        help_text="Motivo de la suspensión del miembro."
    )

class CompanyMemberCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        max_length=150,
        error_messages={
            "required": "El correo es obligatorio",
            "invalid": "Formato de correo no válido"
        }
    )
    password = serializers.CharField(
        required=True,
        min_length=8,
        max_length=100,
        error_messages={
            "required": "La contraseña es obligatoria",
            "min_length": "La contraseña debe tener al menos 8 caracteres"
        }
    )
    role_code = serializers.CharField(
        required=True,
        max_length=50
    )
    nombres = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=True,
        allow_null=True
    )
    apellidos = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=True,
        allow_null=True
    )
