from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from apps.accounts.utils.log_utils import mask_email
import logging

logger = logging.getLogger(__name__)

@shared_task(
    name='apps.accounts.tasks.send_verification_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_verification_email_task(self, email: str, nombres: str, plain_token: str):
    """
    Celery task to send a verification email asynchronously.
    """
    masked = mask_email(email)
    logger.info(f"Iniciando envío de correo de verificación a {masked}")
    
    # Read frontend host URL from settings
    frontend_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:8080').rstrip('/')
    verification_link = f"{frontend_url}/verify-email?token={plain_token}"
    
    context = {
        'nombres': nombres,
        'verification_link': verification_link,
    }
    
    try:
        # Render HTML content
        html_message = render_to_string('accounts/verify_email.html', context)
        # Strip HTML for plain text fallback
        plain_message = strip_tags(html_message)
        
        subject = "Activa tu cuenta - Plataforma Digital"
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Correo de verificación enviado exitosamente a {masked}")
        return f"Email sent successfully to {email}"
        
    except Exception as exc:
        logger.error(f"Error enviando correo a {masked}: {exc}")
        # Retry task in case of transient issues (SMTP failure, etc.)
        raise self.retry(exc=exc)
