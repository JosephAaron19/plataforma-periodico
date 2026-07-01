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


@shared_task(
    name='apps.purchases.tasks.send_subscription_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_subscription_email_task(self, compra_id: int, template_type: str):
    """
    Celery task to send early purchase or automatic activation notifications to the user and admin.
    """
    logger.info(f"send_subscription_email_task: Iniciando envío de correo '{template_type}' para compra_id={compra_id}")
    
    try:
        compra = Compra.objects.using('periodico_db').select_related('usuario', 'edicion').get(id=compra_id)
        pago = Pago.objects.using('periodico_db').filter(compra=compra).order_by('-numero_intento').first()
        
        user = compra.usuario
        full_name = f"{user.nombres} {user.apellidos or ''}".strip()
        email = user.usr_correo
        
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
            period = "Pago único"

        payment_method = pago.medio_pago if (pago and pago.medio_pago) else "YAPE"
        reference_number = pago.identificador_externo if (pago and pago.identificador_externo) else compra.referencia_interna

        # Access dates if activated
        from apps.access.models.acceso_edicion import AccesoEdicion
        acceso = AccesoEdicion.objects.using('periodico_db').filter(compra_id=compra.id, estado='ACTIVO').first()
        
        start_date_str = acceso.fecha_inicio.strftime('%d/%m/%Y %I:%M %p') if acceso else ""
        end_date_str = acceso.fecha_fin.strftime('%d/%m/%Y %I:%M %p') if (acceso and acceso.fecha_fin) else "Acceso Permanente"

        context = {
            'compra_id': compra.id,
            'full_name': full_name,
            'email': email,
            'plan_name': plan_name,
            'period': period,
            'payment_method': payment_method,
            'reference_number': reference_number,
            'price': str(compra.monto_total),
            'start_date': start_date_str,
            'end_date': end_date_str,
        }

        if template_type == 'EARLY_PURCHASE':
            html_message = render_to_string('purchases/early_purchase_email.html', context)
            subject = f"Confirmación de Compra Anticipada: {plan_name} - Amazonia Diario"
        elif template_type == 'ACTIVATED_AUTOMATICALLY':
            html_message = render_to_string('purchases/activation_email.html', context)
            subject = f"¡Tu Suscripción ya está Activa!: {plan_name} - Amazonia Diario"
        else:
            logger.error(f"send_subscription_email_task: Tipo de plantilla desconocido '{template_type}'")
            return f"Unknown template type '{template_type}'"

        plain_message = strip_tags(html_message)
        recipient_list = [email, 'admin@amazoniadiario.com']
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

        # Log notification sent event in audit log (using system origin reference)
        from apps.audit.services.audit_service import AuditService
        AuditService.record_event(
            usuario=user,
            modulo='M11',
            accion='NOTIFICACION_ENVIADA',
            entidad='com_compra',
            entidad_id=str(compra.id),
            valores_nuevos={'tipo_correo': template_type, 'correo_destino': email},
            resultado='EXITOSO',
            motivo=f"Notificación de suscripción '{template_type}' enviada correctamente a {email}."
        )

        logger.info(f"send_subscription_email_task: Correo enviado exitosamente a {email}.")
        return f"Subscription email '{template_type}' sent for purchase={compra_id}"

    except Compra.DoesNotExist:
        logger.error(f"send_subscription_email_task: Compra con id={compra_id} no existe.")
        return f"Compra {compra_id} not found."
    except Exception as exc:
        logger.error(f"send_subscription_email_task: Error al enviar correo de suscripción para compra_id={compra_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)

