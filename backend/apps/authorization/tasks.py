import logging
import hashlib
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.authorization.models.invitacion_usuario import InvitacionUsuario

logger = logging.getLogger(__name__)

def mask_email(email: str) -> str:
    """
    Masks the email prefix for secure logging.
    """
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    name = parts[0]
    domain = parts[1]
    if len(name) <= 2:
        masked_name = name + '***'
    else:
        masked_name = name[:2] + '***'
    return f"{masked_name}@{domain}"

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='apps.authorization.tasks.send_company_invitation_email_task'
)
def send_company_invitation_email_task(self, invitation_id: str, plain_token: str):
    """
    Asynchronously sends an invitation email to a user with a secure signup link.
    """
    try:
        invitation = InvitacionUsuario.objects.using('periodico_db').select_related(
            'empresa', 'invitado_por', 'rol'
        ).get(id=invitation_id)
    except InvitacionUsuario.DoesNotExist:
        logger.error(f"Invitacion {invitation_id} no encontrada en base de datos. Abortando envio.")
        return False

    masked = mask_email(invitation.correo)
    logger.info(f"Iniciando envio de correo para invitacion {invitation_id} a {masked}")

    # Build the accept invitation URL
    frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:8080').rstrip('/')
    accept_link = f"{frontend_base}/accept-invitation?token={plain_token}"

    subject = f"Invitación a unirse a {invitation.empresa.nombre_comercial}"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
                <h2 style="color: #0056b3;">¡Hola!</h2>
                <p>Has sido invitado por <strong>{invitation.invitado_por.get_full_name()}</strong> para unirte a <strong>{invitation.empresa.nombre_comercial}</strong> con el rol de <strong>{invitation.rol.nombre}</strong>.</p>
                <p>Para aceptar esta invitación e ingresar a la plataforma, por favor haz clic en el siguiente botón:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{accept_link}" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Aceptar Invitación</a>
                </p>
                <p style="font-size: 0.9em; color: #666;">Este enlace de invitación expirará el {invitation.fecha_expiracion.strftime('%d/%m/%Y a las %H:%M %Z')}.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
                <p style="font-size: 0.8em; color: #999;">Si no esperabas esta invitación o consideras que se trata de un error, puedes ignorar este correo con seguridad.</p>
            </div>
        </body>
    </html>
    """
    
    text_body = f"""
    ¡Hola!
    Has sido invitado por {invitation.invitado_por.get_full_name()} para unirte a {invitation.empresa.nombre_comercial} con el rol de {invitation.rol.nombre}.
    Para aceptar esta invitación, visita el siguiente enlace: {accept_link}
    Este enlace de invitación expirará el {invitation.fecha_expiracion.strftime('%d/%m/%Y a las %H:%M %Z')}.
    """

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@periodico.com')

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[invitation.correo]
        )
        email.attach_alternative(html_body, "text/html")
        email.send()
        
        logger.info(f"Correo de invitacion enviado exitosamente a {masked}")
        return True
    except Exception as exc:
        logger.error(f"Error al enviar correo de invitacion a {masked}. Reintentando. Detalle: {str(exc)}")
        try:
            self.retry(exc=exc)
        except Exception as retry_exc:
            # Bubble up the retry exception to let Celery manage task state
            raise retry_exc
