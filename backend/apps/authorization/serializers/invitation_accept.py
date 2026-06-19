from rest_framework import serializers

class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        help_text="Token plano recibido en la invitación."
    )
    password = serializers.CharField(
        required=False,
        write_only=True,
        min_length=8,
        help_text="Contraseña para nuevos usuarios."
    )
    nombres = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Nombres para nuevos usuarios."
    )
    apellidos = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=True,
        allow_null=True,
        help_text="Apellidos para nuevos usuarios."
    )
