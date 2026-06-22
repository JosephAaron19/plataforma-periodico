"""
MyPurchasesView — GET /api/v1/my-purchases/

Returns the authenticated user's purchase history.
Excludes: internal tokens, raw gateway payloads, sensitive card data.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.purchases.models.compra import Compra
from apps.purchases.serializers.purchase_serializers import MyPurchaseItemSerializer

logger = logging.getLogger(__name__)


class MyPurchasesView(APIView):
    """
    GET /api/v1/my-purchases/

    Returns the list of purchases for the authenticated user.
    Each item includes: edition, company, date, status, amount, currency,
    active access id, and expiry date (if applicable).

    Does NOT return: internal tokens, raw gateway payloads, full card data,
    CVV, or any sensitive provider credentials.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Only return current user's purchases — no IDOR possible
        compras = (
            Compra.objects.using('periodico_db')
            .select_related('edicion', 'empresa')
            .filter(usuario_id=user.id)
            .order_by('-fecha_creacion')
        )

        serializer = MyPurchaseItemSerializer(compras, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
