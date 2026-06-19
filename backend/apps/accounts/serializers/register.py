from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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
        if not value:
            raise serializers.ValidationError("El correo electrónico es obligatorio")
        return value.strip().lower()

    def validate_numero_documento(self, value):
        if value:
            return value.strip()
        return value

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        nombres = attrs.get('nombres', '')
        apellidos = attrs.get('apellidos', '')
        
        # Instantiate dummy user to run password similarity and strength validation
        dummy_user = Usuario(usr_correo=email, nombres=nombres, apellidos=apellidos)
        try:
            validate_password(password, dummy_user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return attrs

