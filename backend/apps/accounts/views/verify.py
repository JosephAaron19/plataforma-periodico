import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.verify import EmailVerifySerializer
from apps.accounts.services.verification_service import verify_email

logger = logging.getLogger(__name__)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
            
        token = serializer.validated_data['token']
        
        try:
            verify_email(plain_token=token, ip_address=ip_address)
            
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
