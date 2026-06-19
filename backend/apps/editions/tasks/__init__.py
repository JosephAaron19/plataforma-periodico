import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from apps.editions.models.edicion_programacion import EdicionProgramacion
from apps.editions.models.edicion import Edicion
from apps.editions.constants import EstadoEdicion
from apps.editions.services.edition_publish_service import publish_edition

logger = logging.getLogger(__name__)

@shared_task(name="apps.editions.tasks.publish_scheduled_editions_task")
def publish_scheduled_editions_task():
    """
    Idempotent background task to execute publication of editions that have reached their scheduled time.
    Uses select_for_update to guarantee only one worker executes each programacion and prevents double publishing.
    """
    now = timezone.now()
    
    # Get all pending schedulings that are due
    pending_scheds = EdicionProgramacion.objects.using('periodico_db').filter(
        estado='PENDIENTE',
        fecha_programada__lte=now
    ).select_related('edicion')

    processed_count = 0
    
    for sched in pending_scheds:
        try:
            with transaction.atomic(using='periodico_db'):
                # 1. Lock scheduling record and re-verify state
                locked_sched = EdicionProgramacion.objects.using('periodico_db').select_for_update().get(id=sched.id)
                if locked_sched.estado != 'PENDIENTE':
                    logger.warning(f"Scheduling {sched.id} already processed or canceled. Skipping.")
                    continue

                # 2. Lock edition and verify it is still in PROGRAMADA state
                locked_edition = Edicion.objects.using('periodico_db').select_for_update().get(id=locked_sched.edicion.id)
                if locked_edition.estado != EstadoEdicion.PROGRAMADA:
                    # Update scheduling record to error/rejected because the edition state changed
                    locked_sched.estado = 'VENCIDA'
                    locked_sched.resultado = 'RECHAZADO'
                    locked_sched.detalle_error = f"La edición no está en estado PROGRAMADA. Estado actual: '{locked_edition.estado}'."
                    locked_sched.save(using='periodico_db')
                    continue

                # 3. Publish the edition via the service
                publish_edition(
                    company_id=locked_edition.empresa_id,
                    edition_id=locked_edition.id,
                    proceso_origen='CELERY_TASK'
                )

                processed_count += 1

        except Exception as e:
            logger.error(f"Error publishing scheduled edition programacion {sched.id}: {str(e)}", exc_info=True)
            # Try to log the failure in the scheduling record in an isolated transaction
            try:
                with transaction.atomic(using='periodico_db'):
                    failed_sched = EdicionProgramacion.objects.using('periodico_db').select_for_update().get(id=sched.id)
                    if failed_sched.estado == 'PENDIENTE':
                        failed_sched.estado = 'ERROR'
                        failed_sched.resultado = 'ERROR'
                        failed_sched.detalle_error = str(e)
                        failed_sched.save(using='periodico_db')
            except Exception as inner_e:
                logger.error(f"Could not save scheduling error state for {sched.id}: {str(inner_e)}")

    return f"Processed {processed_count} scheduled editions successfully."
