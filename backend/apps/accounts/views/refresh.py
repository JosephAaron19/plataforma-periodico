import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.accounts.serializers.refresh import TokenRefreshSerializer
from apps.accounts.services.refresh_service import refresh_user_tokens
from apps.audit.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        refresh_token = serializer.validated_data['refresh']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        access_token, new_refresh_token = refresh_user_tokens(
            refresh_token_str=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response(
            {
                "access": access_token,
                "refresh": new_refresh_token
            },
            status=status.HTTP_200_OK
        )
