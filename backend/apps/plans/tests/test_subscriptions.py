from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone as django_timezone
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from contextlib import contextmanager

from apps.accounts.models.usuario import Usuario
from apps.plans.models.plan import Plan
from apps.purchases.models.compra import Compra
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.plans.services.user_plan_service import (
    check_user_has_active_plan,
    create_user_plan_purchase,
    activate_user_pending_subscriptions
)

@contextmanager
def dummy_atomic(*args, **kwargs):
    yield

class SubscriptionServiceTests(SimpleTestCase):
    def setUp(self):
        self.user = Usuario(id=1, usr_correo="reader@example.com", nombres="John", apellidos="Doe", estado="ACTIVO")
        self.plan = Plan(id=5, codigo="PLAN_MENSUAL", nombre="Plan Mensual", precio=Decimal("14.50"), moneda="PEN", periodicidad="MENSUAL")

    @patch('apps.plans.services.user_plan_service.AccesoEdicion.objects.using')
    def test_check_user_has_active_plan_exists(self, mock_acceso_using):
        mock_qs = MagicMock()
        mock_qs.filter.return_value.filter.return_value.order_by.return_value.first.return_value = MagicMock(id=100)
        mock_acceso_using.return_value = mock_qs

        res = check_user_has_active_plan(usuario_id=1)
        self.assertIsNotNone(res)

    @patch('apps.plans.services.user_plan_service.AccesoEdicion.objects.using')
    def test_check_user_has_active_plan_none(self, mock_acceso_using):
        mock_qs = MagicMock()
        mock_qs.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_acceso_using.return_value = mock_qs

        res = check_user_has_active_plan(usuario_id=1)
        self.assertIsNone(res)

    @patch('apps.plans.services.user_plan_service.transaction.atomic')
    @patch('apps.plans.services.user_plan_service.check_user_has_active_plan')
    @patch('apps.plans.services.user_plan_service.Compra.objects.using')
    @patch('apps.plans.services.user_plan_service.Pago.objects.using')
    @patch('apps.plans.services.user_plan_service.Edicion.objects.using')
    @patch('apps.plans.services.user_plan_service.ProveedorPago.objects.using')
    @patch('apps.plans.services.user_plan_service.AuditService.record_event')
    def test_create_user_plan_purchase_no_active_plan(
        self, mock_record_event, mock_prov_using, mock_edicion_using, mock_pago_using, mock_compra_using, mock_check_active, mock_atomic
    ):
        mock_atomic.return_value = dummy_atomic()
        mock_check_active.return_value = None

        mock_compra_qs = MagicMock()
        mock_compra_qs.filter.return_value.first.return_value = None
        
        mock_compra = MagicMock(id=10, referencia_interna="MOCK-SUB-PLAN_MENSUAL-XYZ", estado="PENDIENTE")
        mock_compra_qs.create.return_value = mock_compra
        mock_compra_using.return_value = mock_compra_qs

        mock_edicion = MagicMock(id=99, empresa_id=1)
        mock_edicion_qs = MagicMock()
        mock_edicion_qs.filter.return_value.first.return_value = mock_edicion
        mock_edicion_using.return_value = mock_edicion_qs

        mock_prov = MagicMock(id=2, codigo="MOCK", estado="ACTIVO")
        mock_prov_qs = MagicMock()
        mock_prov_qs.get.return_value = mock_prov
        mock_prov_using.return_value = mock_prov_qs

        mock_pago_qs = MagicMock()
        mock_pago_using.return_value = mock_pago_qs

        compra = create_user_plan_purchase(
            usuario=self.user,
            plan=self.plan,
            payment_method='YAPE',
            reference_number='XYZ'
        )

        self.assertEqual(compra, mock_compra)
        mock_compra_qs.create.assert_called_once()
        mock_pago_qs.create.assert_called_once()
        mock_record_event.assert_called_once_with(
            usuario=self.user,
            emp_id=1,
            modulo='M11',
            accion='COMPRA_REALIZADA',
            entidad='com_compra',
            entidad_id='10',
            valores_nuevos={'com_id': 10, 'plan_codigo': 'PLAN_MENSUAL', 'precio': '14.50', 'estado': 'PENDIENTE'},
            resultado='EXITOSO',
            motivo='Compra de plan iniciada exitosamente.'
        )

    @patch('apps.plans.services.user_plan_service.transaction.atomic')
    @patch('apps.plans.services.user_plan_service.check_user_has_active_plan')
    @patch('apps.plans.services.user_plan_service.Compra.objects.using')
    @patch('apps.plans.services.user_plan_service.Pago.objects.using')
    @patch('apps.plans.services.user_plan_service.Edicion.objects.using')
    @patch('apps.plans.services.user_plan_service.ProveedorPago.objects.using')
    @patch('apps.plans.services.user_plan_service.AuditService.record_event')
    def test_create_user_plan_purchase_with_active_plan(
        self, mock_record_event, mock_prov_using, mock_edicion_using, mock_pago_using, mock_compra_using, mock_check_active, mock_atomic
    ):
        mock_atomic.return_value = dummy_atomic()
        mock_check_active.return_value = MagicMock(id=99)

        mock_compra_qs = MagicMock()
        mock_compra_qs.filter.return_value.first.return_value = None

        mock_compra = MagicMock(id=10, referencia_interna="MOCK-SUB-PLAN_MENSUAL-XYZ", estado="PENDIENTE")
        mock_compra_qs.create.return_value = mock_compra
        mock_compra_using.return_value = mock_compra_qs

        mock_edicion = MagicMock(id=99, empresa_id=1)
        mock_edicion_qs = MagicMock()
        mock_edicion_qs.filter.return_value.first.return_value = mock_edicion
        mock_edicion_using.return_value = mock_edicion_qs

        mock_prov = MagicMock(id=2, codigo="MOCK", estado="ACTIVO")
        mock_prov_qs = MagicMock()
        mock_prov_qs.get.return_value = mock_prov
        mock_prov_using.return_value = mock_prov_qs

        mock_pago_qs = MagicMock()
        mock_pago_using.return_value = mock_pago_qs

        compra = create_user_plan_purchase(
            usuario=self.user,
            plan=self.plan,
            payment_method='YAPE',
            reference_number='XYZ'
        )

        self.assertEqual(compra, mock_compra)
        mock_record_event.assert_any_call(
            usuario=self.user,
            emp_id=1,
            modulo='M11',
            accion='COMPRA_PENDIENTE',
            entidad='com_compra',
            entidad_id='10',
            valores_nuevos={'com_id': 10},
            resultado='EXITOSO',
            motivo='Compra marcada como pendiente de activación porque ya existe un plan activo.'
        )

    @patch('apps.plans.services.user_plan_service.transaction.atomic')
    @patch('apps.plans.services.user_plan_service.check_user_has_active_plan')
    @patch('apps.plans.services.user_plan_service.Usuario.objects.using')
    @patch('apps.plans.services.user_plan_service.AccesoTipo.objects.using')
    @patch('apps.plans.services.user_plan_service.Compra.objects.using')
    @patch('apps.plans.services.user_plan_service.AccesoEdicion.objects.using')
    @patch('apps.plans.services.user_plan_service.Edicion.objects.using')
    @patch('apps.plans.services.user_plan_service.AuditService.record_event')
    @patch('apps.purchases.tasks.receipt_email_tasks.send_subscription_email_task.delay')
    def test_activate_user_pending_subscriptions_success(
        self, mock_send_email_delay, mock_record_event, mock_edicion_using, mock_acceso_using, mock_compra_using, mock_tipo_using, mock_user_using, mock_check_active, mock_atomic
    ):
        mock_atomic.return_value = dummy_atomic()
        mock_check_active.return_value = None

        # Mock Usuario
        mock_user_qs = MagicMock()
        mock_user_qs.get.return_value = self.user
        mock_user_using.return_value = mock_user_qs

        # Mock AccesoTipo
        mock_tipo_qs = MagicMock()
        mock_tipo_qs.get.return_value = MagicMock(id=300)
        mock_tipo_using.return_value = mock_tipo_qs

        queued_compra = MagicMock(
            id=12,
            referencia_interna="MOCK-SUB-PLAN_MENSUAL-XYZ",
            monto_total=Decimal("14.50"),
            moneda="PEN",
            usuario=self.user,
            empresa_id=2
        )
        mock_compra_qs = MagicMock()
        mock_compra_qs.filter.return_value.filter.return_value.order_by.return_value.first.return_value = queued_compra
        mock_compra_using.return_value = mock_compra_qs

        placeholder_edicion = MagicMock(id=50, empresa_id=2)
        mock_edicion_qs = MagicMock()
        mock_edicion_qs.filter.return_value.first.return_value = placeholder_edicion
        mock_edicion_using.return_value = mock_edicion_qs

        created_access = MagicMock(id=200)
        mock_acceso_qs = MagicMock()
        mock_acceso_qs.create.return_value = created_access
        # Mock filter().order_by().first() to return None for previous_plan
        mock_acceso_qs.filter.return_value.order_by.return_value.first.return_value = None
        mock_acceso_using.return_value = mock_acceso_qs

        mock_now = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_end = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('django.utils.timezone.now', return_value=mock_now):
            res = activate_user_pending_subscriptions(usuario_id=1)

        self.assertEqual(res, 1)
        queued_compra.save.assert_called_once()
        self.assertTrue(queued_compra.acceso_habilitado)
        
        mock_record_event.assert_called_once_with(
            usuario=self.user,
            emp_id=2,
            modulo='M11',
            accion='COMPRA_ACTIVADA_AUTOMATICAMENTE',
            entidad='com_compra',
            entidad_id='12',
            valores_nuevos={
                'com_id': 12,
                'acc_id': 200,
                'fecha_inicio': mock_now.isoformat(),
                'fecha_fin': mock_end.isoformat()
            },
            resultado='EXITOSO',
            motivo='Suscripción pendiente activada exitosamente.'
        )
        mock_send_email_delay.assert_called_once_with(12, 'ACTIVATED_AUTOMATICALLY')
