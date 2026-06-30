import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.accounts.serializers.password_reset import PasswordResetRequestSerializer
from apps.accounts.services.password_reset_service import request_password_reset
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            exists = request_password_reset(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if exists:
                return Response(
                    {
                        "exists": True,
                        "message": "Se ha enviado un correo con instrucciones para restablecer tu contraseña."
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "exists": False,
                        "message": "El correo ingresado no se encuentra registrado."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            if hasattr(e, 'detail') or isinstance(e, ValueError):
                raise e
            logger.error(f"Error inesperado al solicitar restablecimiento de contraseña: {e}", exc_info=True)
            return Response(
                {"error": "Ocurrió un error inesperado al procesar la solicitud"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
