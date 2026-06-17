from rest_framework import serializers
from apps.accounts.models.usuario import Usuario

class UserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        error_messages={
            "min_length": "La contraseña debe tener al menos 8 caracteres"
        }
    )
    nombres = serializers.CharField(required=True, max_length=100)
    apellidos = serializers.CharField(required=False, allow_blank=True, max_length=100)
    tipo_documento = serializers.CharField(required=False, allow_blank=True, max_length=20)
    numero_documento = serializers.CharField(required=False, allow_blank=True, max_length=20)
    telefono = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if Usuario.objects.filter(usr_correo=normalized_email).exists():
            raise serializers.ValidationError("El correo electrónico ya se encuentra registrado")
        return normalized_email

    def validate_numero_documento(self, value):
        if value:
            # Only validate if not empty
            val = value.strip()
            if Usuario.objects.filter(numero_documento=val).exists():
                raise serializers.ValidationError("El número de documento ya se encuentra registrado")
            return val
        return value
