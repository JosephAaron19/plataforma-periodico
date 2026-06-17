import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.register import UserRegisterSerializer
from apps.accounts.services.register_service import register_user
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
            
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
                ip_address=ip_address,
                user_agent=user_agent
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
