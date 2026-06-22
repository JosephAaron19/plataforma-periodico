import json
import hmac
import hashlib
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.payments.views.webhook_views import PaymentWebhookView
from apps.payments.services.webhook_service import process_webhook_event
from apps.payments.providers.base import NormalizedWebhookEvent
from apps.payments.models.pago import Pago
from apps.payments.models.pago_evento import PagoEvento
from apps.purchases.models.compra import Compra

# ──────────────────────────────────────────────────────────────────────────── #
#                                 WEBHOOK TESTS
# ──────────────────────────────────────────────────────────────────────────── #

class PaymentWebhookTest(SimpleTestCase):
    """
    Tests the webhook receiving logic, cryptographic signature validation,
    and idempotency. Database operations are mocked out completely.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = PaymentWebhookView.as_view()
        self.secret = 'MOCK_SECRET'
        self.payload = {
            "event_id": "evt_test123",
            "type": "payment.success",
            "payment_id": "MOCK-REF-123",
            "amount": "10.00",
            "currency": "PEN"
        }
        self.payload_bytes = json.dumps(self.payload).encode('utf-8')
        self.signature = hmac.new(
            self.secret.encode('utf-8'),
            self.payload_bytes,
            hashlib.sha256
        ).hexdigest()

    @patch('apps.payments.views.webhook_views.get_payment_provider')
    @patch('apps.payments.views.webhook_views.AuditService.record_event')
    @patch('apps.payments.views.webhook_views.process_webhook_event')
    def test_webhook_valid_signature(self, mock_process, mock_audit, mock_get_provider):
        """A webhook with a valid signature is processed successfully."""
        provider = MagicMock()
        provider.validate_webhook_signature.return_value = True
        provider.PROVIDER_CODE = 'MOCK'
        provider.normalize_webhook_event.return_value = NormalizedWebhookEvent(
            event_id="evt_test123",
            type="payment.success",
            external_reference="MOCK-REF-123",
            status="CONFIRMADO",
            amount=Decimal("10.00"),
            currency="PEN",
            raw_payload=self.payload
        )
        mock_get_provider.return_value = provider
        mock_process.return_value = {'status': 'ok'}

        request = self.factory.post('/api/v1/payments/webhook/', data=self.payload, format='json')
        request.META['HTTP_X_MOCK_SIGNATURE'] = self.signature

        response = self.view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')
        mock_process.assert_called_once()
        # Verify audit logs
        mock_audit.assert_called_with(
            usuario=None,
            proceso_origen='WEBHOOK_SYSTEM',
            modulo='M11',
            accion='WEBHOOK_RECIBIDO',
            entidad=None,
            entidad_id=None,
            resultado='EXITOSO',
            motivo='Webhook recibido con firma válida.',
            ip_address=request.META['REMOTE_ADDR'],
            user_agent=''
        )

    @patch('apps.payments.views.webhook_views.get_payment_provider')
    @patch('apps.payments.views.webhook_views.AuditService.record_event')
    def test_webhook_invalid_signature(self, mock_audit, mock_get_provider):
        """A webhook with an invalid signature is rejected immediately (403)."""
        provider = MagicMock()
        provider.validate_webhook_signature.return_value = False
        mock_get_provider.return_value = provider

        request = self.factory.post('/api/v1/payments/webhook/', data=self.payload, format='json')
        request.META['HTTP_X_MOCK_SIGNATURE'] = 'invalid_signature'

        response = self.view(request)
        self.assertEqual(response.status_code, 403)
        mock_audit.assert_called_once()
        self.assertEqual(mock_audit.call_args[1]['accion'], 'WEBHOOK_FIRMA_INVALIDA')


# ──────────────────────────────────────────────────────────────────────────── #
#                          WEBHOOK SERVICE TESTS
# ──────────────────────────────────────────────────────────────────────────── #

class WebhookServiceTest(SimpleTestCase):
    """
    Tests the business logic of webhook processing:
    Idempotency, status matching, and transactional confirmation/rejection.
    """

    def setUp(self):
        self.event = NormalizedWebhookEvent(
            event_id="evt_test123",
            type="payment.success",
            external_reference="MOCK-REF-123",
            status="CONFIRMADO",
            amount=Decimal("10.00"),
            currency="PEN",
            raw_payload={"card_number": "1234567812345678", "other": "data"}
        )

    @patch('apps.payments.services.webhook_service.ProveedorPago.objects')
    @patch('apps.payments.services.webhook_service.PagoEvento.objects')
    @patch('apps.payments.services.webhook_service.Pago.objects')
    @patch('apps.payments.services.webhook_service.Compra.objects')
    @patch('apps.payments.services.webhook_service.transaction.atomic')
    @patch('apps.payments.services.webhook_service.grant_purchase_access')
    @patch('apps.payments.services.webhook_service.AuditService.record_event')
    def test_process_success_grants_access(self, mock_audit, mock_grant, mock_atomic, mock_compra_objs, mock_pago_objs, mock_pago_evento_objs, mock_proveedor_objs):
        """If webhook indicates success and matches exactly, payment is confirmed and access granted."""
        # Setup mocks
        mock_atomic.return_value.__enter__.return_value = None
        
        provider = MagicMock()
        mock_proveedor_objs.using.return_value.get.return_value = provider
        
        pago_evento_instance = MagicMock()
        mock_pago_evento_objs.using.return_value.create.return_value = pago_evento_instance

        # Find payment mock
        pago_instance = MagicMock()
        pago_instance.monto = Decimal("10.00")
        pago_instance.moneda = "PEN"
        pago_instance.estado = Pago.CREADO
        mock_pago_objs.using.return_value.filter.return_value.first.return_value = pago_instance

        # Lock mock
        mock_compra_objs.using.return_value.select_for_update.return_value.get.return_value = pago_instance.compra
        mock_pago_objs.using.return_value.select_for_update.return_value.get.return_value = pago_instance
        
        acceso_mock = MagicMock()
        acceso_mock.id = 999
        mock_grant.return_value = acceso_mock

        # Run
        result = process_webhook_event(self.event, 'MOCK')

        # Assertions
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(pago_instance.estado, Pago.CONFIRMADO)
        self.assertEqual(pago_instance.compra.estado, Compra.PAGADO)
        self.assertTrue(pago_instance.compra.acceso_habilitado)
        mock_grant.assert_called_once()
        self.assertEqual(pago_evento_instance.estado_procesamiento, PagoEvento.PROCESADO)

    @patch('apps.payments.services.webhook_service.ProveedorPago.objects')
    @patch('apps.payments.services.webhook_service.PagoEvento.objects')
    @patch('apps.payments.services.webhook_service.Pago.objects')
    @patch('apps.payments.services.webhook_service.Compra.objects')
    @patch('apps.payments.services.webhook_service.transaction.atomic')
    @patch('apps.payments.services.webhook_service.AuditService.record_event')
    def test_process_mismatch_amount_rejects(self, mock_audit, mock_atomic, mock_compra_objs, mock_pago_objs, mock_pago_evento_objs, mock_proveedor_objs):
        """If webhook amount does not match the database, it rejects the confirmation."""
        mock_atomic.return_value.__enter__.return_value = None
        
        provider = MagicMock()
        mock_proveedor_objs.using.return_value.get.return_value = provider
        
        pago_evento_instance = MagicMock()
        mock_pago_evento_objs.using.return_value.create.return_value = pago_evento_instance

        # Database has 15.00, webhook says 10.00
        pago_instance = MagicMock()
        pago_instance.monto = Decimal("15.00")
        pago_instance.moneda = "PEN"
        pago_instance.estado = Pago.CREADO
        mock_pago_objs.using.return_value.filter.return_value.first.return_value = pago_instance

        mock_compra_objs.using.return_value.select_for_update.return_value.get.return_value = pago_instance.compra
        mock_pago_objs.using.return_value.select_for_update.return_value.get.return_value = pago_instance
        
        # Run
        result = process_webhook_event(self.event, 'MOCK')

        # Assertions
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Mismatched amount or currency')
        self.assertEqual(pago_evento_instance.estado_procesamiento, PagoEvento.FALLIDO)

    @patch('apps.payments.services.webhook_service.ProveedorPago.objects')
    @patch('apps.payments.services.webhook_service.PagoEvento.objects')
    @patch('apps.payments.services.webhook_service.transaction.atomic')
    @patch('apps.payments.services.webhook_service.AuditService.record_event')
    def test_process_idempotent_duplicate_event(self, mock_audit, mock_atomic, mock_pago_evento_objs, mock_proveedor_objs):
        """If event insertion throws IntegrityError, handles idempotency gracefully."""
        mock_atomic.return_value.__enter__.return_value = None
        mock_proveedor_objs.using.return_value.get.return_value = MagicMock()
        
        from django.db import IntegrityError
        # Simulate IntegrityError on event creation
        mock_pago_evento_objs.using.return_value.create.side_effect = IntegrityError()

        # Run
        result = process_webhook_event(self.event, 'MOCK')

        # Assertions
        self.assertEqual(result['status'], 'ok')
        self.assertTrue(result['idempotent'])
        mock_audit.assert_called_once()
        self.assertEqual(mock_audit.call_args[1]['accion'], 'WEBHOOK_EVENTO_DUPLICADO')

    def test_sanitize_payload(self):
        """Verifies that sensitive data is removed from raw payload."""
        from apps.payments.services.webhook_service import _sanitize_payload
        
        raw = {
            "user_id": 123,
            "card_number": "4111222233334444",
            "metadata": {
                "CVV": "123",
                "safe": "data"
            }
        }
        sanitized = _sanitize_payload(raw)
        self.assertEqual(sanitized['user_id'], 123)
        self.assertEqual(sanitized['card_number'], '[REDACTED]')
        self.assertEqual(sanitized['metadata']['CVV'], '[REDACTED]')
        self.assertEqual(sanitized['metadata']['safe'], 'data')
