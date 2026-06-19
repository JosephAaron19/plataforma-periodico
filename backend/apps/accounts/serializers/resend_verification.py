from rest_framework import serializers

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        error_messages={
            "required": "El correo electrónico es obligatorio",
            "invalid": "Ingrese un correo electrónico válido",
            "blank": "El correo electrónico no puede estar vacío"
        }
    )
