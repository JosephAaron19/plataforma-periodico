import logging

logger = logging.getLogger(__name__)

def send_verification_email(*, email: str, nombres: str, plain_token: str) -> None:
    """
    Invokes the Celery task to asynchronously send the verification email to the user.
    """
    from apps.accounts.tasks.send_email import send_verification_email_task
    
    logger.info(f"Encolando envío de correo de verificación para el correo {email}")
    send_verification_email_task.delay(
        email=email,
        nombres=nombres,
        plain_token=plain_token
    )
