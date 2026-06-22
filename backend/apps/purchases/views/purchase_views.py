"""
PurchaseEditionView — POST /api/v1/editions/{edi_id}/purchase/

Initiates a purchase of an individual edition.
All amounts and company info are taken from server-side data only.
No amount or company data from the request body is processed.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError

from apps.editions.models.edicion import Edicion
from apps.purchases.services.purchase_service import initiate_purchase
from apps.purchases.serializers.purchase_serializers import PurchaseInitiateResponseSerializer

logger = logging.getLogger(__name__)


class PurchaseEditionView(APIView):
    """
    POST /api/v1/editions/{edi_id}/purchase/

    Initiates a purchase of a specific edition.
    Requires authenticated and active user.
    All financial amounts are calculated server-side.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, edi_id):
        user = request.user

        if not user.is_active:
            return Response(
                {'detail': 'Tu cuenta no está activa.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            edicion = Edicion.objects.using('periodico_db').select_related(
                'empresa', 'empresa__empresa_plan'
            ).prefetch_related('paginas').get(id=edi_id)
        except Edicion.DoesNotExist:
            return Response(
                {'detail': 'Edición no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            result = initiate_purchase(
                usuario=user,
                edicion=edicion,
                request=request,
                using='periodico_db'
            )
        except ValidationError as e:
            message = e.message if hasattr(e, 'message') else str(e)
            # Clean up Django ValidationError list format
            if isinstance(message, list):
                message = ' '.join(str(m) for m in message)
            return Response(
                {'detail': message},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            logger.error(
                f"PurchaseEditionView: Error inesperado edi={edi_id} usr={user.id}: {e}",
                exc_info=True
            )
            return Response(
                {'detail': 'Error interno al procesar la compra.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = PurchaseInitiateResponseSerializer(result)
        http_status = status.HTTP_200_OK if result['already_exists'] else status.HTTP_201_CREATED
        return Response(serializer.data, status=http_status)
