from rest_framework import serializers

class CompanyInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        max_length=150,
        help_text="Correo electrónico del usuario a invitar."
    )
    role_code = serializers.CharField(
        required=True,
        max_length=50,
        help_text="Código del rol empresarial a asignar."
    )
    mensaje = serializers.CharField(
        required=False,
        max_length=500,
        allow_blank=True,
        allow_null=True,
        help_text="Mensaje personalizado opcional."
    )
