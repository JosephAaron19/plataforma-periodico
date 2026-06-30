import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.purchases.models.compra import Compra
from apps.payments.models.pago import Pago
from apps.purchases.services.purchase_service import confirm_purchase_mock
from apps.authorization.services.permission_service import is_platform_superadmin

logger = logging.getLogger(__name__)

class IsPlatformAdmin(IsAuthenticated):
    """
    Permission class that grants access only to superadmins or platform admins.
    """
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False
        return is_platform_superadmin(request.user) or getattr(request.user, 'usr_correo', '') == 'admin'


class AdminPendingPurchasesView(APIView):
    """
    GET /api/v1/purchases/admin/pending/

    Lists purchases with their user details, reference number, plan details,
    and receipt upload image URL. Supports filtering via status query param.
    """
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        try:
            status_param = request.query_params.get('status', 'todos').lower()

            compras = (
                Compra.objects.using('periodico_db')
                .select_related('usuario', 'edicion', 'empresa')
                .order_by('-fecha_creacion')
            )

            if status_param == 'pendiente':
                compras = compras.filter(estado=Compra.PENDIENTE)
            elif status_param == 'aprobado':
                compras = compras.filter(estado=Compra.PAGADO)  # 'PAGADA'
            elif status_param == 'rechazado':
                compras = compras.filter(estado=Compra.RECHAZADO)  # 'RECHAZADA'

            data = []
            for compra in compras:
                pago = Pago.objects.using('periodico_db').filter(
                    compra=compra
                ).order_by('-numero_intento').first()

                # Extract screenshot path from payment response message
                comprobante_url = None
                if pago and pago.mensaje_respuesta and "Screenshot comprobante guardado en: " in pago.mensaje_respuesta:
                    path = pago.mensaje_respuesta.split("Screenshot comprobante guardado en: ")[1]
                    comprobante_url = request.build_absolute_uri(settings.MEDIA_URL + path)

                # Parse plan code
                plan_code = 'mensual'
                ref_upper = compra.referencia_interna.upper()
                if "DIARIO" in ref_upper:
                    plan_code = 'diario'
                elif "ANUAL" in ref_upper:
                    plan_code = 'anual'
                elif "EDITION_" in ref_upper or compra.referencia_interna.startswith("REF-") and not any(p in ref_upper for p in ["MENSUAL", "ANUAL", "DIARIO"]):
                    plan_code = f"edition_{compra.edicion_id}"

                data.append({
                    'com_id': compra.id,
                    'fecha_creacion': compra.fecha_creacion,
                    'monto': compra.monto_total,
                    'moneda': compra.moneda,
                    'plan_code': plan_code,
                    'estado': compra.estado,
                    'usuario': {
                        'id': compra.usuario.id,
                        'nombres': compra.usuario.nombres,
                        'apellidos': compra.usuario.apellidos,
                        'correo': compra.usuario.usr_correo
                    },
                    'pago': {
                        'medio_pago': pago.medio_pago if pago else 'YAPE',
                        'identificador_externo': pago.identificador_externo if pago else compra.referencia_interna,
                        'comprobante_url': comprobante_url
                    }
                })

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"AdminPendingPurchasesView: Error al listar pendientes: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno al obtener el listado de pendientes.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminValidatePurchaseView(APIView):
    """
    POST /api/v1/purchases/admin/validate/

    Approves (validates and confirms) or rejects a pending payment receipt.
    """
    permission_classes = [IsPlatformAdmin]

    def post(self, request):
        com_id = request.data.get('com_id')
        action = request.data.get('action')  # 'approve' or 'reject'

        if not com_id or action not in ['approve', 'reject']:
            return Response(
                {'detail': 'Faltan parámetros obligatorios: com_id y action (approve/reject).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            compra = Compra.objects.using('periodico_db').get(id=com_id)
        except Compra.DoesNotExist:
            return Response(
                {'detail': 'La compra especificada no existe.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if compra.estado != Compra.PENDIENTE:
            return Response(
                {'detail': f'La compra no está pendiente (estado actual: {compra.estado}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if action == 'approve':
            try:
                # confirm_purchase_mock updates states to PAGADA/APROBADO, grants access and fires celery email
                result = confirm_purchase_mock(
                    com_id=compra.id,
                    using='periodico_db'
                )
                logger.info(f"AdminValidatePurchaseView: Compra {com_id} aprobada con éxito.")
                return Response({
                    'detail': 'Pago verificado y comprobante enviado exitosamente al usuario.',
                    'result': result
                }, status=status.HTTP_200_OK)

            except ValidationError as ve:
                return Response(
                    {'detail': str(ve)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"AdminValidatePurchaseView: Error al aprobar compra={com_id}: {e}", exc_info=True)
                return Response(
                    {'detail': 'Error interno al convalidar el pago.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        elif action == 'reject':
            try:
                pago = Pago.objects.using('periodico_db').filter(
                    compra=compra,
                    estado=Pago.CREADO
                ).order_by('-numero_intento').first()

                with transaction.atomic(using='periodico_db'):
                    compra.estado = Compra.RECHAZADO
                    compra.save(using='periodico_db')

                    if pago:
                        pago.estado = Pago.RECHAZADO
                        pago.save(using='periodico_db')

                logger.info(f"AdminValidatePurchaseView: Compra {com_id} rechazada por el administrador.")
                return Response(
                    {'detail': 'Pago rechazado exitosamente.'},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                logger.error(f"AdminValidatePurchaseView: Error al rechazar compra={com_id}: {e}", exc_info=True)
                return Response(
                    {'detail': 'Error interno al rechazar el pago.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


from datetime import timedelta
from django.utils import timezone

class AdminSubscribersListView(APIView):
    """
    GET /api/v1/purchases/admin/subscribers/

    Lists users who have a confirmed plan purchase (subscriber list).
    """
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        try:
            compras = (
                Compra.objects.using('periodico_db')
                .select_related('usuario', 'empresa')
                .filter(estado='PAGADA')
                .order_by('-fecha_confirmacion')
            )

            data = []
            for compra in compras:
                ref_upper = (compra.referencia_interna or '').upper()
                plan_code = None
                plan_name = None
                duration_days = 0

                if "DIARIO" in ref_upper:
                    plan_code = 'diario'
                    plan_name = 'Plan Diario'
                    duration_days = 1
                elif "MENSUAL" in ref_upper:
                    plan_code = 'mensual'
                    plan_name = 'Plan Mensual'
                    duration_days = 30
                elif "ANUAL" in ref_upper:
                    plan_code = 'anual'
                    plan_name = 'Plan Anual'
                    duration_days = 365

                # Only include plan subscribers, not individual edition purchases
                if not plan_code:
                    continue

                start_date = compra.fecha_confirmacion or compra.fecha_creacion
                expiration_date = start_date + timedelta(days=duration_days)
                
                # Check status
                is_active = timezone.now() < expiration_date
                sub_status = 'ACTIVO' if is_active else 'VENCIDO'

                pago = Pago.objects.using('periodico_db').filter(
                    compra=compra
                ).order_by('-numero_intento').first()

                data.append({
                    'id': compra.id,
                    'plan_code': plan_code,
                    'plan_name': plan_name,
                    'fecha_inicio': start_date,
                    'fecha_vencimiento': expiration_date,
                    'estado': sub_status,
                    'monto': compra.monto_total,
                    'moneda': compra.moneda,
                    'usuario': {
                        'id': compra.usuario.id,
                        'nombres': compra.usuario.nombres,
                        'apellidos': compra.usuario.apellidos,
                        'correo': compra.usuario.usr_correo
                    },
                    'pago_metodo': pago.medio_pago if pago else 'YAPE',
                    'referencia': pago.identificador_externo if pago else compra.referencia_interna
                })

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"AdminSubscribersListView: Error: {e}", exc_info=True)
            return Response(
                {'detail': 'Error interno al obtener la lista de suscriptores.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
