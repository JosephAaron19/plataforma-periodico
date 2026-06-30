from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "required": "El correo electrónico es obligatorio",
            "blank": "El correo electrónico no puede estar vacío"
        }
    )
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "required": "La contraseña es obligatoria",
            "blank": "La contraseña no puede estar vacía"
        }
    )
