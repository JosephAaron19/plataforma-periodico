import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.verify import EmailVerifySerializer
from apps.accounts.services.verification_service import verify_email
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
            
        token = serializer.validated_data['token']
        
        try:
            verify_email(plain_token=token, ip_address=ip_address, user_agent=user_agent)
            
            return Response(
                {
                    "message": "Correo verificado correctamente. Usuario activado."
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Re-raise validation errors so DRF handles them with appropriate 400 status
            if hasattr(e, 'detail') or isinstance(e, ValueError):
                raise e
            
            logger.error(f"Error inesperado durante la verificación de correo: {e}", exc_info=True)
            return Response(
                {"error": "Ocurrió un error inesperado al verificar el correo electrónico"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
