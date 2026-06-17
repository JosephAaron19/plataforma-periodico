import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.register import UserRegisterSerializer
from apps.accounts.services.register_service import register_user

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
            
        validated_data = serializer.validated_data
        
        try:
            register_user(
                email=validated_data['email'],
                password=validated_data['password'],
                nombres=validated_data['nombres'],
                apellidos=validated_data.get('apellidos'),
                tipo_documento=validated_data.get('tipo_documento'),
                numero_documento=validated_data.get('numero_documento'),
                telefono=validated_data.get('telefono'),
                ip_address=ip_address
            )
            
            return Response(
                {
                    "message": "Usuario registrado correctamente. Revisa tu correo para activar la cuenta."
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error inesperado durante el registro: {e}", exc_info=True)
            return Response(
                {"error": "Ocurrió un error inesperado al registrar el usuario"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
