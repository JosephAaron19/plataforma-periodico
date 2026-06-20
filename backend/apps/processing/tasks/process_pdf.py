import logging
from celery import shared_task
from apps.processing.services.pdf_processor import process_pdf_attempt
from apps.processing.exceptions import TransientProcessingError

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=10,
    default_retry_delay=60,
    soft_time_limit=300,
    time_limit=360,
    name='apps.processing.tasks.process_edition_pdf_task'
)
def process_edition_pdf_task(self, intento_id: int):
    """
    Celery task that triggers processing for a PDF upload attempt.
    Supports dynamic retries for transient errors.
    """
    logger.info(f"Iniciando tarea Celery process_edition_pdf_task para intento_id={intento_id}")
    try:
        process_pdf_attempt(intento_id)
        return True
    except TransientProcessingError as err:
        countdown = 60 * (2 ** err.attempt_number)
        logger.warning(
            f"Error transitorio en intento {intento_id}. "
            f"Reintentando con nuevo intento_id={err.new_intento_id} en {countdown} segundos. Detalle: {str(err)}"
        )
        try:
            self.retry(args=[err.new_intento_id], countdown=countdown)
        except Exception as retry_exc:
            raise retry_exc
    except Exception as exc:
        logger.exception(f"Error crítico no controlado en Celery para intento_id={intento_id}: {str(exc)}")
        raise exc
