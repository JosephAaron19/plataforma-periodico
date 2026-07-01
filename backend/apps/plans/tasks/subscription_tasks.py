import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from apps.purchases.models.compra import Compra
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.plans.services.user_plan_service import activate_user_pending_subscriptions

logger = logging.getLogger(__name__)

@shared_task(
    name='apps.plans.tasks.activate_expired_subscriptions_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def activate_expired_subscriptions_task(self):
    """
    Celery Beat task that scans for users with expired active plans
    and triggers activation for their queued plans.
    """
    logger.info("activate_expired_subscriptions_task: Starting scan for expired user subscriptions.")
    now = timezone.now()
    
    try:
        # Find distinct users who have queued purchases
        queued_purchases = Compra.objects.using('periodico_db').filter(
            estado=Compra.PAGADO,
            acceso_habilitado=False
        ).filter(
            Q(referencia_interna__icontains='DIARIO') |
            Q(referencia_interna__icontains='MENSUAL') |
            Q(referencia_interna__icontains='ANUAL')
        )
        
        user_ids = queued_purchases.values_list('usuario_id', flat=True).distinct()
        activated_count = 0
        
        for user_id in user_ids:
            # Check if user has an active plan (not expired yet)
            has_active = AccesoEdicion.objects.using('periodico_db').filter(
                usuario_id=user_id,
                estado='ACTIVO',
                origen_referencia__in=['PLAN_DIARIO', 'PLAN_MENSUAL', 'PLAN_ANUAL'],
                fecha_inicio__lte=now
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=now)
            ).exists()
            
            if not has_active:
                logger.info(f"activate_expired_subscriptions_task: User {user_id} active plan has expired/non-existent. Activating queued plan.")
                res = activate_user_pending_subscriptions(usuario_id=user_id, using='periodico_db')
                if res > 0:
                    activated_count += 1
                    
        logger.info(f"activate_expired_subscriptions_task: Scan completed. Activated {activated_count} queued subscriptions.")
        return f"Activated {activated_count} queued plan subscriptions"
        
    except Exception as exc:
        logger.error(f"activate_expired_subscriptions_task: Error scanning/activating subscriptions: {exc}", exc_info=True)
        raise self.retry(exc=exc)
