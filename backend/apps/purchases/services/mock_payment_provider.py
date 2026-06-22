"""
MockPaymentProvider — proveedor de pago simulado para desarrollo y pruebas.

Este proveedor NO conecta servicios externos reales.
Solo genera respuestas controladas para facilitar el flujo de pruebas interno.

Para integración con Culqi, Stripe, PayPal u otra pasarela real,
implementar una clase equivalente siguiendo la misma interfaz.
"""
import uuid


class MockPaymentResult:
    """Result object returned by the mock payment provider."""

    def __init__(self, success: bool, external_id: str, message: str, code: str = None):
        self.success = success
        self.external_id = external_id
        self.message = message
        self.code = code

    def __repr__(self):
        return f"MockPaymentResult(success={self.success}, external_id={self.external_id!r})"


class MockPaymentProvider:
    """
    Simulated payment provider for development/test environments only.

    Behavior:
      - By default: always returns success (simulate approved payment).
      - force_failure=True: returns a controlled rejection response.

    This provider is identified in ppr_proveedor_pago by ppr_codigo='MOCK'.
    """
    PROVIDER_CODE = 'MOCK'

    def __init__(self, force_failure: bool = False):
        self._force_failure = force_failure

    def initiate_payment(self, *, amount, currency, reference) -> MockPaymentResult:
        """
        Initiates a mock payment. Returns a MockPaymentResult.
        The external_id simulates the token a real gateway would return.

        NOTE: Never pass raw card data here. This mock does not accept it by design.
        """
        external_id = f"MOCK-{uuid.uuid4().hex[:16].upper()}"
        if self._force_failure:
            return MockPaymentResult(
                success=False,
                external_id=external_id,
                message="Pago rechazado por simulación (force_failure=True).",
                code="MOCK_REJECTED"
            )
        return MockPaymentResult(
            success=True,
            external_id=external_id,
            message="Pago aprobado por proveedor mock.",
            code="MOCK_APPROVED"
        )

    def confirm_payment(self, *, external_id: str) -> MockPaymentResult:
        """
        Confirms a previously initiated mock payment.
        In a real gateway this would call the confirmation API endpoint.
        """
        if self._force_failure:
            return MockPaymentResult(
                success=False,
                external_id=external_id,
                message="Confirmación rechazada por simulación.",
                code="MOCK_CONFIRM_REJECTED"
            )
        return MockPaymentResult(
            success=True,
            external_id=external_id,
            message="Pago confirmado correctamente por proveedor mock.",
            code="MOCK_CONFIRMED"
        )
