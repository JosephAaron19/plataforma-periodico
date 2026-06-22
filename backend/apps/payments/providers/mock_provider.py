import json
import uuid
import hmac
import hashlib
from decimal import Decimal
from django.conf import settings

from apps.payments.providers.base import BasePaymentProvider, PaymentResult, NormalizedWebhookEvent


class MockPaymentProvider(BasePaymentProvider):
    """
    Simulated payment provider for development/test environments only.
    Identified in ppr_proveedor_pago by ppr_codigo='MOCK'.
    """
    PROVIDER_CODE = 'MOCK'

    def __init__(self, force_failure: bool = False):
        self._force_failure = force_failure

    def initiate_payment(self, *, amount: Decimal, currency: str, reference: str) -> PaymentResult:
        external_id = f"MOCK-{uuid.uuid4().hex[:16].upper()}"
        if self._force_failure:
            return PaymentResult(
                success=False,
                external_id=external_id,
                message="Pago rechazado por simulación (force_failure=True).",
                code="MOCK_REJECTED"
            )
        return PaymentResult(
            success=True,
            external_id=external_id,
            message="Pago aprobado por proveedor mock.",
            code="MOCK_APPROVED"
        )

    def confirm_payment(self, *, external_id: str) -> PaymentResult:
        if self._force_failure:
            return PaymentResult(
                success=False,
                external_id=external_id,
                message="Confirmación rechazada por simulación.",
                code="MOCK_CONFIRM_REJECTED"
            )
        return PaymentResult(
            success=True,
            external_id=external_id,
            message="Pago confirmado correctamente por proveedor mock.",
            code="MOCK_CONFIRMED"
        )

    def validate_webhook_signature(self, request) -> bool:
        """
        Mock signature validation.
        Validates using HMAC-SHA256 with PAYMENT_WEBHOOK_SECRET over request.body.
        Also expects a 'X-Mock-Signature' header.
        """
        secret_key = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', 'MOCK_SECRET')
        signature_header = request.META.get('HTTP_X_MOCK_SIGNATURE')
        
        if not signature_header:
            return False

        # Calculate expected signature
        expected_sig = hmac.new(
            secret_key.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)

    def normalize_webhook_event(self, request) -> NormalizedWebhookEvent:
        """
        Parses a mock webhook payload.
        Expected format:
        {
            "event_id": "evt_...",
            "type": "payment.success" or "payment.failed",
            "payment_id": "MOCK-...",
            "amount": "10.00",
            "currency": "PEN"
        }
        """
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

        event_id = payload.get('event_id')
        event_type = payload.get('type')
        payment_id = payload.get('payment_id')
        
        if not event_id or not event_type or not payment_id:
            raise ValueError("Missing required fields in mock webhook payload")

        # Map status
        if event_type == 'payment.success':
            status = 'CONFIRMADO'
        elif event_type == 'payment.failed':
            status = 'RECHAZADO'
        else:
            status = 'IGNORADO'

        try:
            amount = Decimal(str(payload.get('amount', '0')))
        except Exception:
            amount = Decimal('0')

        return NormalizedWebhookEvent(
            event_id=event_id,
            type=event_type,
            external_reference=payment_id,
            status=status,
            amount=amount,
            currency=payload.get('currency', 'PEN'),
            raw_payload=payload
        )
