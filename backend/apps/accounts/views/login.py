import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.login import LoginSerializer
from apps.accounts.services.login_service import authenticate_and_create_session
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        access_token, refresh_token, user = authenticate_and_create_session(
            email=email,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response(
            {
                "access": access_token,
                "refresh": refresh_token,
                "token_type": "Bearer",
                "expires_in": 900,
                "user": {
                    "id": user.id,
                    "email": user.usr_correo,
                    "nombres": user.nombres,
                    "apellidos": user.apellidos
                }
            },
            status=status.HTTP_200_OK
        )
