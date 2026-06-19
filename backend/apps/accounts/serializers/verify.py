from rest_framework import serializers

class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField(required=True, allow_blank=False, error_messages={
        "required": "El token de verificación es obligatorio",
        "blank": "El token de verificación no puede estar vacío"
    })
