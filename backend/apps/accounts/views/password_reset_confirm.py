import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.accounts.serializers.password_reset import PasswordResetConfirmSerializer
from apps.accounts.services.password_reset_service import confirm_password_reset
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        try:
            confirm_password_reset(
                plain_token=token,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return Response(
                {
                    "message": "Contraseña actualizada correctamente. Ahora puedes iniciar sesión."
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            if hasattr(e, 'detail') or isinstance(e, ValueError):
                raise e
            logger.error(f"Error inesperado al restablecer contraseña: {e}", exc_info=True)
            return Response(
                {"error": "Ocurrió un error inesperado al restablecer la contraseña"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
