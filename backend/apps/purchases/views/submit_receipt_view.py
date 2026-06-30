import logging
import uuid
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction

from apps.editions.models.edicion import Edicion
from apps.purchases.models.compra import Compra
from apps.purchases.models.proveedor_pago import ProveedorPago
from apps.payments.models.pago import Pago

logger = logging.getLogger(__name__)

class SubmitReceiptView(APIView):
    """
    POST /api/v1/purchases/submit-receipt/

    Registers a pending purchase and payment screenshot for verification.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_active:
            return Response(
                {'detail': 'Tu cuenta no está activa.'},
                status=status.HTTP_403_FORBIDDEN
            )

        plan_code = request.data.get('plan_code', 'mensual')
        payment_method = request.data.get('payment_method', 'yape')
        reference_number = request.data.get('reference_number', '').strip()
        receipt_image = request.FILES.get('receipt_image')

        if not reference_number:
            return Response(
                {'detail': 'El número de referencia es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not receipt_image:
            return Response(
                {'detail': 'El comprobante de pago es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Determine product / plan price & target edition
        edition = None
        price = Decimal('14.50')  # Default monthly
        description = "Suscripción Mensual"

        if plan_code.startswith('edition_'):
            try:
                edi_id = int(plan_code.replace('edition_', ''))
                edition = Edicion.objects.using('periodico_db').get(id=edi_id)
                price = edition.precio
                description = f"Edición Digital: {edition.titulo}"
            except (ValueError, Edicion.DoesNotExist):
                return Response(
                    {'detail': 'Edición no encontrada.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Plan pricing fallbacks
            if plan_code == 'diario':
                price = Decimal('0.50')
                description = "Plan Diario"
            elif plan_code == 'anual':
                price = Decimal('129.00')
                description = "Plan Anual"
            elif plan_code == 'mensual':
                price = Decimal('14.50')
                description = "Plan Mensual"

            # Fetch a placeholder active edition (since edi_id cannot be null)
            edition = Edicion.objects.using('periodico_db').filter(estado='PUBLICADA').first()
            if not edition:
                edition = Edicion.objects.using('periodico_db').first()
            
            if not edition:
                return Response(
                    {'detail': 'No hay ediciones disponibles en el sistema para asociar la suscripción.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 2. Build reference key for idempotency
        ref_key = f"REF-{reference_number}-{plan_code.upper()}"

        try:
            # Check if purchase already exists
            existing_compra = Compra.objects.using('periodico_db').filter(
                referencia_interna=ref_key,
                usuario=user
            ).first()

            if existing_compra:
                logger.info(f"SubmitReceiptView: Compra idempotente encontrada para ref={ref_key}")
                existing_pago = Pago.objects.using('periodico_db').filter(
                    compra=existing_compra
                ).order_by('-numero_intento').first()

                return Response({
                    'com_id': existing_compra.id,
                    'pag_id': existing_pago.id if existing_pago else None,
                    'estado': existing_compra.estado,
                    'monto': existing_compra.monto_total,
                    'moneda': existing_compra.moneda,
                    'descripcion': description,
                    'already_exists': True
                }, status=status.HTTP_200_OK)

            # Get mock provider
            try:
                proveedor = ProveedorPago.objects.using('periodico_db').get(codigo='MOCK', estado='ACTIVO')
            except ProveedorPago.DoesNotExist:
                # Create a mock provider if not exists
                proveedor = ProveedorPago.objects.using('periodico_db').first()

            if not proveedor:
                return Response(
                    {'detail': 'Proveedor de pago MOCK no configurado.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 3. Save receipt image to media folder
            sanitized_filename = f"receipts/{uuid.uuid4().hex}_{receipt_image.name}"
            saved_path = default_storage.save(sanitized_filename, receipt_image)

            with transaction.atomic(using='periodico_db'):
                # 4. Create Compra
                compra = Compra.objects.using('periodico_db').create(
                    usuario=user,
                    empresa_id=edition.empresa_id,
                    edicion=edition,
                    referencia_interna=ref_key,
                    precio_unitario=price,
                    monto_total=price,
                    moneda='PEN',
                    estado=Compra.PENDIENTE,
                    origen=Compra.ORIGEN_WEB,
                    acceso_habilitado=False,
                )

                # 5. Create Pago
                pago = Pago.objects.using('periodico_db').create(
                    compra=compra,
                    proveedor=proveedor,
                    numero_intento=1,
                    identificador_externo=reference_number,
                    monto=price,
                    moneda='PEN',
                    estado=Pago.CREADO,
                    medio_pago=payment_method.upper(),
                    mensaje_respuesta=f"Screenshot comprobante guardado en: {saved_path}"
                )

            logger.info(f"SubmitReceiptView: Compra {compra.id} y Pago {pago.id} creados para ref={ref_key}")

            return Response({
                'com_id': compra.id,
                'pag_id': pago.id,
                'estado': compra.estado,
                'monto': compra.monto_total,
                'moneda': compra.moneda,
                'descripcion': description,
                'already_exists': False
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"SubmitReceiptView: Error inesperado al procesar comprobante: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno al registrar el comprobante.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
