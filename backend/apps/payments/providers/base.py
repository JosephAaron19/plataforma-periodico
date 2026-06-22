import abc
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PaymentResult:
    """Result object returned by payment providers."""
    success: bool
    external_id: str
    message: str
    code: Optional[str] = None


@dataclass
class NormalizedWebhookEvent:
    """Standardized representation of a webhook event from any provider."""
    event_id: str  # Unique event ID for idempotency (e.g. evt_123)
    type: str  # Original provider event type (e.g. payment_intent.succeeded)
    external_reference: str  # The ID of the payment this event refers to (e.g. pi_123)
    status: str  # Mapped to our internal states: CONFIRMADO, RECHAZADO, etc.
    amount: Decimal
    currency: str
    raw_payload: Dict[str, Any]  # Should be sanitized


class BasePaymentProvider(abc.ABC):
    """
    Abstract base class for all payment providers.
    Enforces a strict interface that shields the core logic from provider-specific details.
    """
    PROVIDER_CODE: str

    @abc.abstractmethod
    def initiate_payment(self, *, amount: Decimal, currency: str, reference: str) -> PaymentResult:
        """Initiates a payment intention. Returns a PaymentResult."""
        pass

    @abc.abstractmethod
    def confirm_payment(self, *, external_id: str) -> PaymentResult:
        """Synchronously confirms a payment via API call to the provider."""
        pass

    @abc.abstractmethod
    def validate_webhook_signature(self, request) -> bool:
        """
        Validates the cryptographic signature of the incoming webhook.
        Must use request.body (raw bytes) to guarantee integrity.
        """
        pass

    @abc.abstractmethod
    def normalize_webhook_event(self, request) -> NormalizedWebhookEvent:
        """
        Parses the webhook payload and standardizes it into a NormalizedWebhookEvent.
        """
        pass
