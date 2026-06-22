import logging
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.payments.models.pago import Pago
from apps.payments.models.pago_evento import PagoEvento
from apps.purchases.models.compra import Compra
from apps.purchases.models.proveedor_pago import ProveedorPago
from apps.audit.services.audit_service import AuditService
from apps.purchases.services.grant_access_service import grant_purchase_access
from apps.payments.providers.base import NormalizedWebhookEvent

logger = logging.getLogger(__name__)
AUDIT_MODULE = 'M11'

def _sanitize_payload(payload: dict) -> dict:
    """Removes sensitive keys from the raw payload before saving to DB."""
    if not isinstance(payload, dict):
        return {}
    sanitized = payload.copy()
    sensitive_keys = ['card_number', 'cvv', 'token', 'authorization', 'signature']
    for k in list(sanitized.keys()):
        if any(sec in k.lower() for sec in sensitive_keys):
            sanitized[k] = '[REDACTED]'
        elif isinstance(sanitized[k], dict):
            sanitized[k] = _sanitize_payload(sanitized[k])
    return sanitized

def process_webhook_event(event: NormalizedWebhookEvent, provider_code: str, request=None, using: str = 'periodico_db') -> dict:
    """
    Processes a standardized webhook event.
    Returns a dict with processing result.
    """
    ip_address = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
        if request else None
    )
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else None

    # 1. Resolve Provider
    try:
        proveedor = ProveedorPago.objects.using(using).get(codigo=provider_code)
    except ProveedorPago.DoesNotExist:
        logger.error(f"Proveedor {provider_code} no encontrado.")
        return {'status': 'error', 'message': 'Provider not found', 'idempotent': False}

    # 2. Insert Event for Idempotency
    try:
        with transaction.atomic(using=using):
            pago_evento = PagoEvento.objects.using(using).create(
                proveedor=proveedor,
                identificador_externo=event.event_id,
                tipo_evento=event.type,
                payload=_sanitize_payload(event.raw_payload),
                estado_procesamiento=PagoEvento.RECIBIDO
            )
    except IntegrityError:
        # Event already processed
        AuditService.record_event(
            usuario=None,
            proceso_origen='WEBHOOK_SYSTEM',
            modulo=AUDIT_MODULE,
            accion='WEBHOOK_EVENTO_DUPLICADO',
            entidad='pge_pago_evento',
            entidad_id=event.event_id,
            resultado='EXITOSO',
            motivo='El evento ya fue recibido previamente (idempotencia).',
            ip_address=ip_address,
            user_agent=user_agent
        )
        return {'status': 'ok', 'message': 'Idempotent response, already processed', 'idempotent': True}

    # 3. Find associated payment
    # Depending on provider, external_reference might map to pag_identificador_externo or Compras.referencia_interna
    # For Mock, it's MOCK-REF-{referencia_interna} but wait, in initiate_purchase we didn't set pag_identificador_externo.
    # We need to find the payment. If the gateway returned an external_id on initiate, we use that.
    # For this architecture, we assume external_reference maps to pag_identificador_externo 
    # Or we can look for it in pag_identificador_externo.
    
    pago = Pago.objects.using(using).filter(identificador_externo=event.external_reference).first()
    
    if not pago:
        # Sometimes webhooks arrive before the initiate returns (race condition), but since we initiate first, it should exist.
        # But wait, in initiate_purchase we set identificador_externo=None. Let's fix that in initiate if we can,
        # or we assume external_reference is our internal reference.
        # Let's search by internal reference in Compra if we don't find it in Pago
        compra_by_ref = Compra.objects.using(using).filter(referencia_interna=event.external_reference.replace('MOCK-REF-', '')).first()
        if compra_by_ref:
            pago = Pago.objects.using(using).filter(compra=compra_by_ref).order_by('-numero_intento').first()
            
    if not pago:
        pago_evento.estado_procesamiento = PagoEvento.FALLIDO
        pago_evento.motivo_rechazo = "Pago no encontrado."
        pago_evento.save(using=using)
        logger.error(f"Pago asociado a {event.external_reference} no encontrado.")
        return {'status': 'error', 'message': 'Payment not found', 'idempotent': False}

    pago_evento.pago = pago
    pago_evento.save(using=using)

    compra = pago.compra
    usuario = compra.usuario

    # 4. Transactional Processing
    try:
        with transaction.atomic(using=using):
            # Lock records
            compra = Compra.objects.using(using).select_for_update().get(id=compra.id)
            pago = Pago.objects.using(using).select_for_update().get(id=pago.id)

            if pago.estado in [Pago.CONFIRMADO]:
                # Already confirmed, idempotency at payment level
                pago_evento.estado_procesamiento = PagoEvento.IGNORADO
                pago_evento.motivo_rechazo = "Pago ya estaba confirmado."
                pago_evento.save(using=using)
                return {'status': 'ok', 'message': 'Payment already confirmed', 'idempotent': True}

            # Validate amount and currency
            if event.amount != pago.monto or event.currency != pago.moneda:
                pago_evento.estado_procesamiento = PagoEvento.FALLIDO
                pago_evento.motivo_rechazo = f"Mismatched amount/currency. Expected {pago.monto} {pago.moneda}, got {event.amount} {event.currency}."
                pago_evento.save(using=using)
                
                AuditService.record_event(
                    usuario=None,
                    proceso_origen='WEBHOOK_SYSTEM',
                    modulo=AUDIT_MODULE,
                    accion='WEBHOOK_MONTO_INVALIDO',
                    entidad='pag_pago',
                    entidad_id=str(pago.id),
                    resultado='RECHAZADO',
                    motivo=pago_evento.motivo_rechazo,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return {'status': 'error', 'message': 'Mismatched amount or currency', 'idempotent': False}

            now = timezone.now()

            if event.status == 'CONFIRMADO':
                pago.estado = Pago.CONFIRMADO
                pago.identificador_externo = event.external_reference
                pago.fecha_confirmacion = now
                pago.fecha_actualizacion = now
                pago.save(using=using)

                compra.estado = Compra.PAGADO
                compra.fecha_confirmacion = now
                compra.acceso_habilitado = True
                compra.save(using=using)

                acceso = grant_purchase_access(usuario=usuario, edicion=compra.edicion, compra=compra, using=using)

                pago_evento.estado_procesamiento = PagoEvento.PROCESADO
                pago_evento.fecha_procesamiento = now
                pago_evento.save(using=using)

                AuditService.record_event(
                    usuario=None,
                    proceso_origen='WEBHOOK_SYSTEM',
                    modulo=AUDIT_MODULE,
                    accion='WEBHOOK_PAGO_CONFIRMADO',
                    entidad='pag_pago',
                    entidad_id=str(pago.id),
                    resultado='EXITOSO',
                    motivo='Pago confirmado vía webhook.',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                AuditService.record_event(
                    usuario=usuario, # User gets access
                    emp_id=compra.edicion.empresa_id,
                    modulo=AUDIT_MODULE,
                    accion='ACCESO_COMPRA_CONCEDIDO',
                    entidad='acc_acceso_contenido',
                    entidad_id=str(acceso.id),
                    resultado='EXITOSO',
                    motivo='Acceso de lectura concedido tras validación de webhook.',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            elif event.status == 'RECHAZADO':
                pago.estado = Pago.RECHAZADO
                pago.identificador_externo = event.external_reference
                pago.fecha_actualizacion = now
                pago.save(using=using)

                compra.estado = Compra.RECHAZADO
                compra.save(using=using)

                pago_evento.estado_procesamiento = PagoEvento.PROCESADO
                pago_evento.fecha_procesamiento = now
                pago_evento.save(using=using)

                AuditService.record_event(
                    usuario=None,
                    proceso_origen='WEBHOOK_SYSTEM',
                    modulo=AUDIT_MODULE,
                    accion='WEBHOOK_PAGO_RECHAZADO',
                    entidad='pag_pago',
                    entidad_id=str(pago.id),
                    resultado='RECHAZADO',
                    motivo='Pago rechazado vía webhook.',
                    ip_address=ip_address,
                    user_agent=user_agent
                )

            else:
                pago_evento.estado_procesamiento = PagoEvento.IGNORADO
                pago_evento.motivo_rechazo = f"Estado {event.status} ignorado."
                pago_evento.fecha_procesamiento = now
                pago_evento.save(using=using)

    except Exception as e:
        logger.error(f"Error procesando evento de pago {event.event_id}: {e}", exc_info=True)
        pago_evento.estado_procesamiento = PagoEvento.FALLIDO
        pago_evento.motivo_rechazo = f"Exception: {str(e)}"
        pago_evento.save(using=using)
        
        AuditService.record_event(
            usuario=None,
            proceso_origen='WEBHOOK_SYSTEM',
            modulo=AUDIT_MODULE,
            accion='PAGO_ERROR_PROVEEDOR',
            entidad='pge_pago_evento',
            entidad_id=str(pago_evento.id),
            resultado='ERROR',
            motivo='Error al procesar webhook en base de datos.',
            ip_address=ip_address,
            user_agent=user_agent
        )
        return {'status': 'error', 'message': 'Internal processing error', 'idempotent': False}

    return {'status': 'ok', 'message': 'Processed successfully', 'idempotent': False}
