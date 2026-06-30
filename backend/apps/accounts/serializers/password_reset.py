import re
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'El correo electrónico es obligatorio',
            'invalid': 'Ingresa un correo electrónico válido'
        }
    )

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, error_messages={'required': 'El token de recuperación es obligatorio'})
    password = serializers.CharField(required=True, error_messages={'required': 'La nueva contraseña es obligatoria'})
    confirm_password = serializers.CharField(required=True, error_messages={'required': 'La confirmación de contraseña es obligatoria'})

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("La contraseña debe contener al menos una letra mayúscula")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("La contraseña debe contener al menos un número")
        # Matches any character that is not alphanumeric or space (i.e. symbols)
        if not re.search(r'[^a-zA-Z0-9]', value):
            raise serializers.ValidationError("La contraseña debe contener al menos un símbolo especial")
        return value

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden"})
        
        return data
