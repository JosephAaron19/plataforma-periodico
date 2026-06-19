import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.accounts.serializers.logout import LogoutSerializer
from apps.accounts.services.logout_service import logout_user_session
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        refresh_token = serializer.validated_data['refresh']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        logout_user_session(
            user=request.user,
            refresh_token_str=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response(
            {
                "message": "Sesión cerrada correctamente."
            },
            status=status.HTTP_200_OK
        )
