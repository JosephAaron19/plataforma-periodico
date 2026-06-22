import hmac
import hashlib
from decimal import Decimal
from django.conf import settings

from apps.payments.providers.base import BasePaymentProvider, PaymentResult, NormalizedWebhookEvent


class ExternalPaymentProvider(BasePaymentProvider):
    """
    Base class for real external payment gateways (Stripe, Culqi, PayPal).
    Implements generic cryptographic validation assuming standard HMAC-SHA256 signatures.
    """

    def validate_webhook_signature(self, request) -> bool:
        """
        Generic HMAC-SHA256 validation over the raw request body.
        Requires the gateway's specific header name to be implemented by subclass.
        """
        secret_key = getattr(settings, 'PAYMENT_WEBHOOK_SECRET', None)
        if not secret_key:
            return False
            
        # The specific header name needs to be defined by subclasses
        signature_header_name = getattr(self, 'SIGNATURE_HEADER_NAME', None)
        if not signature_header_name:
            raise NotImplementedError("Subclasses must define SIGNATURE_HEADER_NAME")

        signature_header = request.META.get(signature_header_name)
        if not signature_header:
            return False

        # In real integrations, signatures might come with a timestamp (e.g., Stripe's 't=...,v1=...')
        # This base logic assumes a direct comparison. Subclasses should override if needed.
        expected_sig = hmac.new(
            secret_key.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)

    # Note: initiate_payment, confirm_payment, and normalize_webhook_event
    # must be fully implemented by concrete provider subclasses.
