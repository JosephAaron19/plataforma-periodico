import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from apps.purchases.models.compra import Compra
from apps.payments.models.pago import Pago

logger = logging.getLogger(__name__)

@shared_task(
    name='apps.purchases.tasks.send_receipt_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_receipt_email_task(self, compra_id: int):
    """
    Celery task to send a purchase receipt email to the user and the administrator.
    """
    logger.info(f"send_receipt_email_task: Iniciando envío de comprobante para compra_id={compra_id}")
    
    try:
        compra = Compra.objects.using('periodico_db').select_related('usuario', 'edicion').get(id=compra_id)
        pago = Pago.objects.using('periodico_db').filter(compra=compra).order_by('-numero_intento').first()
        
        user = compra.usuario
        full_name = f"{user.nombres} {user.apellidos or ''}".strip()
        email = user.usr_correo
        
        # 1. Determine plan metadata from referencia_interna
        ref = compra.referencia_interna.upper()
        if "DIARIO" in ref:
            plan_name = "Plan Diario"
            period = "1 día (Edición de hoy)"
        elif "ANUAL" in ref:
            plan_name = "Plan Anual"
            period = "12 meses"
        elif "MENSUAL" in ref:
            plan_name = "Plan Mensual"
            period = "1 mes"
        else:
            plan_name = f"Edición Digital: {compra.edicion.titulo}" if compra.edicion else "Compra de Edición"
            period = "Pago único (Acceso de por vida)"

        payment_method = pago.medio_pago or "YAPE"
        reference_number = pago.identificador_externo or compra.referencia_interna

        # Context for the HTML email
        context = {
            'compra_id': compra.id,
            'full_name': full_name,
            'email': email,
            'plan_name': plan_name,
            'period': period,
            'payment_method': payment_method,
            'reference_number': reference_number,
            'price': str(compra.monto_total),
        }

        # Render HTML message
        html_message = render_to_string('purchases/receipt_email.html', context)
        plain_message = strip_tags(html_message)

        subject = f"Comprobante de compra {context['plan_name']} - Amazonia Diario"
        
        # Recipient list: user and admin
        recipient_list = [email, 'admin@amazoniadiario.com']
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"send_receipt_email_task: Comprobante enviado exitosamente a {email} y admin.")
        return f"Receipt email sent for purchase={compra_id}"

    except Compra.DoesNotExist:
        logger.error(f"send_receipt_email_task: Compra con id={compra_id} no existe.")
        return f"Compra {compra_id} not found."
    except Exception as exc:
        logger.error(f"send_receipt_email_task: Error al enviar comprobante para compra_id={compra_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)
