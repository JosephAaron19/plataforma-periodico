from django.conf import settings
import logging

from apps.payments.providers.base import BasePaymentProvider, PaymentResult, NormalizedWebhookEvent
from apps.payments.providers.mock_provider import MockPaymentProvider
from apps.payments.providers.external_provider import ExternalPaymentProvider

logger = logging.getLogger(__name__)

def get_payment_provider() -> BasePaymentProvider:
    """
    Factory to retrieve the active payment provider based on configuration.
    Falls back to MockPaymentProvider if 'PAYMENT_PROVIDER' is not set or invalid.
    """
    provider_name = getattr(settings, 'PAYMENT_PROVIDER', 'MOCK').upper()
    
    if provider_name == 'MOCK':
        return MockPaymentProvider()
    
    # If a real provider is configured but not implemented, fail safely
    logger.warning(f"Payment provider '{provider_name}' not fully implemented. Falling back to MOCK.")
    return MockPaymentProvider()

__all__ = [
    'BasePaymentProvider',
    'PaymentResult',
    'NormalizedWebhookEvent',
    'MockPaymentProvider',
    'ExternalPaymentProvider',
    'get_payment_provider'
]
