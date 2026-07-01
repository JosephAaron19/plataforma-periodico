import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Q

from apps.purchases.models.compra import Compra
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.plans.models.plan import Plan

logger = logging.getLogger(__name__)

class UserSubscriptionsView(APIView):
    """
    GET /api/v1/user/subscriptions/
    
    Returns the user's active plan subscription, future/queued plan purchases,
    and history of past/expired plan subscriptions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # 1. Fetch active subscription
        active_access = AccesoEdicion.objects.using('periodico_db').filter(
            usuario_id=user.id,
            estado='ACTIVO',
            origen_referencia__in=['PLAN_DIARIO', 'PLAN_MENSUAL', 'PLAN_ANUAL'],
            fecha_inicio__lte=now
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=now)
        ).order_by('-fecha_inicio').first()

        active_data = None
        if active_access:
            compra = None
            if active_access.compra_id:
                try:
                    compra = Compra.objects.using('periodico_db').get(id=active_access.compra_id)
                except Compra.DoesNotExist:
                    pass
            
            plan_name = "Suscripción Activa"
            plan_desc = ""
            price = "0.00"
            moneda = "PEN"
            
            plan_code = active_access.origen_referencia
            try:
                plan = Plan.objects.using('periodico_db').get(codigo=plan_code)
                plan_name = plan.nombre
                plan_desc = plan.descripcion
                price = str(plan.precio)
                moneda = plan.moneda
            except Plan.DoesNotExist:
                if plan_code == 'PLAN_DIARIO':
                    plan_name = "Plan Diario"
                    price = "0.50"
                elif plan_code == 'PLAN_MENSUAL':
                    plan_name = "Plan Mensual"
                    price = "14.50"
                elif plan_code == 'PLAN_ANUAL':
                    plan_name = "Plan Anual"
                    price = "129.00"

            active_data = {
                'id': active_access.id,
                'compra_id': active_access.compra_id,
                'plan_codigo': plan_code,
                'nombre': plan_name,
                'descripcion': plan_desc,
                'fecha_inicio': active_access.fecha_inicio.isoformat(),
                'fecha_fin': active_access.fecha_fin.isoformat() if active_access.fecha_fin else None,
                'estado': active_access.estado,
                'precio': price,
                'moneda': moneda,
                'medio_pago': 'MOCK' if not compra else getattr(compra.pagos.order_by('-numero_intento').first(), 'medio_pago', 'YAPE')
            }

        # 2. Fetch pending / queued purchases
        pending_compras = Compra.objects.using('periodico_db').filter(
            usuario_id=user.id,
            estado__in=[Compra.PENDIENTE, Compra.PAGADO]
        ).filter(
            Q(referencia_interna__icontains='DIARIO') |
            Q(referencia_interna__icontains='MENSUAL') |
            Q(referencia_interna__icontains='ANUAL')
        ).order_by('fecha_creacion')

        pending_list = []
        for c in pending_compras:
            # Exclude currently active one
            if active_access and c.id == active_access.compra_id:
                continue

            # Exclude paid purchases that are already active/granted
            if c.estado == Compra.PAGADO and c.acceso_habilitado:
                continue

            plan_name = "Suscripción Pendiente"
            plan_code = "PLAN_MENSUAL"
            if "DIARIO" in c.referencia_interna.upper():
                plan_name = "Plan Diario"
                plan_code = "PLAN_DIARIO"
            elif "ANUAL" in c.referencia_interna.upper():
                plan_name = "Plan Anual"
                plan_code = "PLAN_ANUAL"

            status_str = "PENDIENTE_PAGO" if c.estado == Compra.PENDIENTE else "PENDIENTE_ACTIVACION"

            pago = c.pagos.order_by('-numero_intento').first()
            medio_pago = pago.medio_pago if (pago and pago.medio_pago) else "YAPE"

            pending_list.append({
                'compra_id': c.id,
                'plan_codigo': plan_code,
                'nombre': plan_name,
                'fecha_creacion': c.fecha_creacion.isoformat(),
                'estado': status_str,
                'precio': str(c.monto_total),
                'moneda': c.moneda,
                'medio_pago': medio_pago
            })

        # 3. Fetch history
        history_accesses = AccesoEdicion.objects.using('periodico_db').filter(
            usuario_id=user.id,
            origen_referencia__in=['PLAN_DIARIO', 'PLAN_MENSUAL', 'PLAN_ANUAL']
        ).exclude(
            id=active_access.id if active_access else -1
        ).order_by('-fecha_inicio')

        history_list = []
        for h in history_accesses:
            plan_name = "Plan Suscripción"
            if h.origen_referencia == 'PLAN_DIARIO':
                plan_name = "Plan Diario"
            elif h.origen_referencia == 'PLAN_MENSUAL':
                plan_name = "Plan Mensual"
            elif h.origen_referencia == 'PLAN_ANUAL':
                plan_name = "Plan Anual"

            history_list.append({
                'id': h.id,
                'compra_id': h.compra_id,
                'plan_codigo': h.origen_referencia,
                'nombre': plan_name,
                'fecha_inicio': h.fecha_inicio.isoformat(),
                'fecha_fin': h.fecha_fin.isoformat() if h.fecha_fin else None,
                'estado': 'EXPIRADO' if (h.fecha_fin and h.fecha_fin <= now) else h.estado,
            })

        return Response({
            'active_subscription': active_data,
            'pending_subscriptions': pending_list,
            'history': history_list
        }, status=status.HTTP_200_OK)
