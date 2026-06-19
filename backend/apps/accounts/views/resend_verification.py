import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.resend_verification import ResendVerificationSerializer
from apps.accounts.services.resend_verification_service import resend_verification_link
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        try:
            resend_verification_link(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Error inesperado durante la solicitud de reenvío de verificación: {e}", exc_info=True)
            
        return Response(
            {
                "message": "Si la cuenta existe y requiere verificación, recibirás un nuevo enlace."
            },
            status=status.HTTP_200_OK
        )
