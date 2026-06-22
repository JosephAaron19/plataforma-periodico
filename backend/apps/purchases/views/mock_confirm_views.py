"""
MockConfirmPaymentView — POST /api/v1/payments/mock-confirm/

INTERNAL ENDPOINT — Solo disponible en entorno de desarrollo (DEBUG=True)
o para usuarios con permiso de superadministrador de plataforma.

Confirma un pago pendiente usando el proveedor mock.
No conecta servicios externos reales.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.purchases.services.purchase_service import confirm_purchase_mock
from apps.purchases.serializers.purchase_serializers import (
    MockConfirmRequestSerializer,
    MockConfirmResponseSerializer,
)
from apps.authorization.services.permission_service import is_platform_superadmin

logger = logging.getLogger(__name__)


class MockConfirmPaymentView(APIView):
    """
    POST /api/v1/payments/mock-confirm/

    Confirms a pending purchase using the mock payment provider.
    Access restricted to DEBUG environments or platform superadmins.

    Body:
        {
          "com_id": <int>,
          "force_failure": <bool, optional, default false>
        }

    This endpoint MUST NOT be exposed publicly in production without
    explicit permission control. It is not a real payment gateway flow.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Restrict access: only DEBUG mode or platform superadmin
        if not settings.DEBUG and not is_platform_superadmin(user):
            return Response(
                {'detail': 'Este endpoint solo está disponible en entorno de desarrollo.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.is_active:
            return Response(
                {'detail': 'Tu cuenta no está activa.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MockConfirmRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        com_id = serializer.validated_data['com_id']
        force_failure = serializer.validated_data.get('force_failure', False)

        try:
            result = confirm_purchase_mock(
                com_id=com_id,
                force_failure=force_failure,
                request=request,
                using='periodico_db'
            )
        except ValidationError as e:
            message = e.message if hasattr(e, 'message') else str(e)
            if isinstance(message, list):
                message = ' '.join(str(m) for m in message)
            return Response(
                {'detail': message},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            logger.error(
                f"MockConfirmPaymentView: Error inesperado com={com_id} usr={user.id}: {e}",
                exc_info=True
            )
            return Response(
                {'detail': 'Error interno al confirmar el pago.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_serializer = MockConfirmResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
