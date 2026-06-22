import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.payments.providers import get_payment_provider
from apps.payments.services.webhook_service import process_webhook_event
from apps.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)
AUDIT_MODULE = 'M11'

class PaymentWebhookView(APIView):
    """
    Endpoint for receiving webhooks from payment providers.
    Does not require JWT authentication, uses cryptographic signature validation.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        provider = get_payment_provider()
        
        ip_address = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # 1. Validate signature
        try:
            is_valid = provider.validate_webhook_signature(request)
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            is_valid = False

        if not is_valid:
            AuditService.record_event(
                usuario=None,
                proceso_origen='WEBHOOK_SYSTEM',
                modulo=AUDIT_MODULE,
                accion='WEBHOOK_FIRMA_INVALIDA',
                entidad=None,
                entidad_id=None,
                resultado='RECHAZADO',
                motivo='Firma criptográfica inválida o ausente.',
                ip_address=ip_address,
                user_agent=user_agent
            )
            return Response({'error': 'Invalid signature'}, status=status.HTTP_403_FORBIDDEN)

        # 2. Audit reception
        AuditService.record_event(
            usuario=None,
            proceso_origen='WEBHOOK_SYSTEM',
            modulo=AUDIT_MODULE,
            accion='WEBHOOK_RECIBIDO',
            entidad=None,
            entidad_id=None,
            resultado='EXITOSO',
            motivo='Webhook recibido con firma válida.',
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 3. Normalize Event
        try:
            event = provider.normalize_webhook_event(request)
        except ValueError as e:
            logger.warning(f"Invalid webhook payload: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Process Event
        result = process_webhook_event(
            event=event,
            provider_code=provider.PROVIDER_CODE,
            request=request
        )

        if result.get('status') == 'ok':
            return Response({'status': 'ok', 'idempotent': result.get('idempotent', False)})
        else:
            # We return 200 even on processing errors like "payment not found" or "mismatched amount"
            # to prevent the provider from retrying indefinitely, unless we want them to retry.
            # But usually 400 is better for mismatched payloads.
            return Response({'error': result.get('message')}, status=status.HTTP_400_BAD_REQUEST)
