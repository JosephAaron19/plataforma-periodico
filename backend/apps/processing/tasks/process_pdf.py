import logging
from celery import shared_task
from apps.processing.services.pdf_processor import process_pdf_attempt

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='apps.processing.tasks.process_edition_pdf_task'
)
def process_edition_pdf_task(self, intento_id: int):
    """
    Celery task that triggers processing for a PDF upload attempt.
    Supports up to 3 retries for transient errors.
    """
    logger.info(f"Iniciando tarea Celery process_edition_pdf_task para intento_id={intento_id}")
    try:
        process_pdf_attempt(intento_id)
        return True
    except Exception as exc:
        logger.warning(f"Error transitorio procesando intento_id={intento_id}. Reintentando Celery... Detalle: {str(exc)}")
        try:
            self.retry(exc=exc)
        except Exception as retry_exc:
            raise retry_exc
