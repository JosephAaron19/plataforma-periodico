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
        compra_id = request.query_params.get('id')

        if compra_id:
            try:
                compra = (
                    Compra.objects.using('periodico_db')
                    .select_related('edicion', 'empresa')
                    .get(usuario_id=user.id, id=compra_id)
                )
                # Fetch related payment details
                pago = compra.pagos.order_by('-numero_intento').first()
                serializer = MyPurchaseItemSerializer(compra)
                data = serializer.data
                if pago:
                    data['medio_pago'] = pago.medio_pago
                    data['identificador_externo'] = pago.identificador_externo
                else:
                    data['medio_pago'] = 'YAPE'
                    data['identificador_externo'] = compra.referencia_interna
                
                # Add user context securely for receipt generation
                data['usuario'] = {
                    'nombres': user.nombres,
                    'apellidos': user.apellidos,
                    'correo': user.usr_correo,
                    'id': user.id
                }
                return Response(data, status=status.HTTP_200_OK)
            except Compra.DoesNotExist:
                return Response(
                    {'detail': 'Compra no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Only return current user's purchases — no IDOR possible
        compras = (
            Compra.objects.using('periodico_db')
            .select_related('edicion', 'empresa')
            .filter(usuario_id=user.id)
            .order_by('-fecha_creacion')
        )

        serializer = MyPurchaseItemSerializer(compras, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
