from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import MagicMock, patch
from datetime import timedelta
from contextlib import contextmanager
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.plans.models.plan import Plan
from apps.plans.models.empresa_plan import EmpresaPlan
from apps.plans.models.plan_funcionalidad import PlanFuncionalidad
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.authorization.models.permiso import Permiso
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.invitacion_usuario import InvitacionUsuario

# Dummy atomic transaction manager for SimpleTestCase (prevents DB access exceptions)
@contextmanager
def dummy_atomic(using=None):
    yield

class PlansAndLimitsTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        
        # Mock users
        self.superadmin = Usuario(id=1, usr_correo="admin@ejemplo.com", nombres="Super", apellidos="Admin", estado="ACTIVO", correo_verificado=True)
        self.regular_user = Usuario(id=2, usr_correo="user@ejemplo.com", nombres="Regular", apellidos="User", estado="ACTIVO", correo_verificado=True)
        
        # Mock company
        self.company = Empresa(id=10, razon_social="Empresa Test", ruc="20123456789", estado="ACTIVA", eliminado=False)
        
        # Mock plans
        self.plan_base = Plan(
            id=100,
            codigo="PLAN_BASE",
            nombre="Plan Base",
            descripcion="Plan inicial comercial",
            precio=50.00,
            moneda="PEN",
            periodicidad="MENSUAL",
            limite_usuarios=5,
            limite_ediciones_mes=10,
            limite_storage_mb=100,
            es_publico=True,
            orden=1,
            estado="ACTIVO"
        )
        self.plan_premium = Plan(
            id=101,
            codigo="PLAN_PREMIUM",
            nombre="Plan Premium",
            precio=150.00,
            moneda="PEN",
            periodicidad="MENSUAL",
            limite_usuarios=20,
            limite_ediciones_mes=100,
            limite_storage_mb=1024,
            es_publico=True,
            orden=2,
            estado="ACTIVO"
        )

    # 1. Selector: Resolution of Active Plan (get_company_active_plan)
    @patch('apps.plans.selectors.plan_selectors.EmpresaPlan.objects.using')
    def test_get_company_active_plan_success(self, mock_ep_using):
        now = timezone.now()
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base, estado='ACTIVO', fecha_inicio=now - timedelta(days=1))
        mock_ep_using.return_value.select_related.return_value.filter.return_value.filter.return_value = [ep]

        from apps.plans.selectors.plan_selectors import get_company_active_plan
        res = get_company_active_plan(10)
        self.assertEqual(res, ep)
        self.assertEqual(res.plan, self.plan_base)

    @patch('apps.plans.selectors.plan_selectors.EmpresaPlan.objects.using')
    def test_get_company_active_plan_inconsistency(self, mock_ep_using):
        now = timezone.now()
        ep1 = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base, estado='ACTIVO', fecha_inicio=now - timedelta(days=1))
        ep2 = EmpresaPlan(id=51, empresa=self.company, plan=self.plan_premium, estado='ACTIVO', fecha_inicio=now - timedelta(days=1))
        mock_ep_using.return_value.select_related.return_value.filter.return_value.filter.return_value = [ep1, ep2]

        from apps.plans.selectors.plan_selectors import get_company_active_plan
        with self.assertRaises(ValidationError) as ctx:
            get_company_active_plan(10)
        self.assertIn("múltiples planes activos", str(ctx.exception))

    @patch('apps.plans.selectors.plan_selectors.EmpresaPlan.objects.using')
    def test_get_company_active_plan_none(self, mock_ep_using):
        mock_ep_using.return_value.select_related.return_value.filter.return_value.filter.return_value = []

        from apps.plans.selectors.plan_selectors import get_company_active_plan
        res = get_company_active_plan(10)
        self.assertIsNone(res)

    # 2. Selector: Active Plans (get_active_plans)
    @patch('apps.plans.selectors.plan_selectors.Plan.objects.using')
    def test_get_active_plans(self, mock_plan_using):
        mock_plan_using.return_value.filter.return_value.order_by.return_value = [self.plan_base, self.plan_premium]

        from apps.plans.selectors.plan_selectors import get_active_plans
        res = get_active_plans()
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].codigo, "PLAN_BASE")

    # 3. Services: plan_feature_service (has_plan_feature)
    @patch('apps.plans.services.plan_feature_service.get_company_active_plan')
    @patch('apps.plans.services.plan_feature_service.PlanFuncionalidad.objects.using')
    def test_has_plan_feature_enabled(self, mock_pf_using, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_pf_using.return_value.filter.return_value.filter.return_value.exists.return_value = True

        from apps.plans.services.plan_feature_service import has_plan_feature
        res = has_plan_feature(self.company, "EDICION_CREAR")
        self.assertTrue(res)

    @patch('apps.plans.services.plan_feature_service.get_company_active_plan')
    @patch('apps.plans.services.plan_feature_service.PlanFuncionalidad.objects.using')
    def test_has_plan_feature_disabled(self, mock_pf_using, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_pf_using.return_value.filter.return_value.filter.return_value.exists.return_value = False

        from apps.plans.services.plan_feature_service import has_plan_feature
        res = has_plan_feature(self.company, "EDICION_ELIMINAR")
        self.assertFalse(res)

    # 4. Services: plan_limit_service - User limits
    @patch('apps.plans.services.plan_limit_service.get_company_active_plan')
    @patch('apps.plans.services.plan_limit_service.get_active_company_members_count')
    def test_check_user_limit_within(self, mock_count, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_count.return_value = 3  # limit is 5

        from apps.plans.services.plan_limit_service import check_user_limit
        res = check_user_limit(self.company)
        self.assertTrue(res["allowed"])
        self.assertEqual(res["limit"], 5)
        self.assertEqual(res["used"], 3)

    @patch('apps.plans.services.plan_limit_service.get_company_active_plan')
    @patch('apps.plans.services.plan_limit_service.get_active_company_members_count')
    def test_check_user_limit_exceeded(self, mock_count, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_count.return_value = 5  # limit is 5

        from apps.plans.services.plan_limit_service import check_user_limit
        res = check_user_limit(self.company)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["code"], "PLAN_USER_LIMIT_REACHED")

    # 5. Services: plan_limit_service - Edition limits
    @patch('apps.plans.services.plan_limit_service.get_company_active_plan')
    @patch('apps.plans.services.plan_limit_service.get_current_month_editions_count')
    def test_check_edition_limit_within(self, mock_count, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_count.return_value = 4  # limit is 10

        from apps.plans.services.plan_limit_service import check_edition_limit
        res = check_edition_limit(self.company)
        self.assertTrue(res["allowed"])

    @patch('apps.plans.services.plan_limit_service.get_company_active_plan')
    @patch('apps.plans.services.plan_limit_service.get_current_month_editions_count')
    def test_check_edition_limit_exceeded(self, mock_count, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_count.return_value = 10  # limit is 10

        from apps.plans.services.plan_limit_service import check_edition_limit
        res = check_edition_limit(self.company)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["code"], "PLAN_EDITION_LIMIT_REACHED")

    # 6. Services: plan_limit_service - Storage limits
    @patch('apps.plans.services.plan_limit_service.get_company_active_plan')
    @patch('apps.plans.services.plan_limit_service.get_company_storage_bytes')
    def test_check_storage_limit_within(self, mock_bytes, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)  # limit is 100MB = 104,857,600 Bytes
        mock_get_active.return_value = ep
        mock_bytes.return_value = 50 * 1024 * 1024  # 50MB used

        from apps.plans.services.plan_limit_service import check_storage_limit
        res = check_storage_limit(self.company, additional_bytes=10 * 1024 * 1024)
        self.assertTrue(res["allowed"])

    @patch('apps.plans.services.plan_limit_service.get_company_active_plan')
    @patch('apps.plans.services.plan_limit_service.get_company_storage_bytes')
    def test_check_storage_limit_exceeded(self, mock_bytes, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)  # limit is 100MB
        mock_get_active.return_value = ep
        mock_bytes.return_value = 95 * 1024 * 1024  # 95MB used

        from apps.plans.services.plan_limit_service import check_storage_limit
        res = check_storage_limit(self.company, additional_bytes=10 * 1024 * 1024)  # requires additional 10MB -> 105MB > 100MB
        self.assertFalse(res["allowed"])
        self.assertEqual(res["code"], "PLAN_STORAGE_LIMIT_REACHED")

    # 7. Services: plan_change_service - Switch plan successfully without overconsumption
    @patch('apps.plans.services.plan_change_service.Empresa.objects.using')
    @patch('apps.plans.services.plan_change_service.get_plan_by_code')
    @patch('apps.plans.services.plan_change_service.EmpresaPlan.objects.using')
    @patch('apps.plans.services.plan_change_service.get_company_usage')
    @patch('apps.plans.services.plan_change_service.EmpresaPlan.save')
    @patch('apps.plans.services.plan_change_service.EmpresaHistorial.save')
    @patch('apps.plans.services.plan_change_service.AuditService.record_event')
    @patch('apps.plans.services.plan_change_service.transaction.atomic', side_effect=dummy_atomic)
    def test_change_company_plan_success(self, mock_atomic, mock_audit, mock_history_save, mock_ep_save, mock_usage, mock_ep_using, mock_get_plan, mock_company_using):
        mock_company_using.return_value.get.return_value = self.company
        mock_get_plan.return_value = self.plan_premium
        mock_ep_using.return_value.select_for_update.return_value.filter.return_value = []
        mock_usage.return_value = {"users": 2, "editions": 5, "storage_bytes": 10 * 1024 * 1024}

        from apps.plans.services.plan_change_service import change_company_plan
        res = change_company_plan(
            empresa_id=10,
            plan_code="PLAN_PREMIUM",
            reason="Prueba exitosa",
            solicitante=self.superadmin,
            ip_address="127.0.0.1"
        )
        self.assertEqual(res.plan, self.plan_premium)
        self.assertEqual(res.estado, 'ACTIVO')
        mock_history_save.assert_called_once()
        mock_audit.assert_called_once()
        
        # Assert audit code matches success
        _, kwargs = mock_audit.call_args
        self.assertEqual(kwargs["accion"], "PLAN_EMPRESA_CAMBIADO")

    # 8. Services: plan_change_service - Switch plan with overconsumption
    @patch('apps.plans.services.plan_change_service.Empresa.objects.using')
    @patch('apps.plans.services.plan_change_service.get_plan_by_code')
    @patch('apps.plans.services.plan_change_service.EmpresaPlan.objects.using')
    @patch('apps.plans.services.plan_change_service.get_company_usage')
    @patch('apps.plans.services.plan_change_service.EmpresaPlan.save')
    @patch('apps.plans.services.plan_change_service.EmpresaHistorial.save')
    @patch('apps.plans.services.plan_change_service.AuditService.record_event')
    @patch('apps.plans.services.plan_change_service.transaction.atomic', side_effect=dummy_atomic)
    def test_change_company_plan_overconsumption(self, mock_atomic, mock_audit, mock_history_save, mock_ep_save, mock_usage, mock_ep_using, mock_get_plan, mock_company_using):
        mock_company_using.return_value.get.return_value = self.company
        mock_get_plan.return_value = self.plan_base  # limit users = 5
        mock_ep_using.return_value.select_for_update.return_value.filter.return_value = []
        mock_usage.return_value = {"users": 8, "editions": 5, "storage_bytes": 10 * 1024 * 1024} # 8 > 5 users!

        from apps.plans.services.plan_change_service import change_company_plan
        res = change_company_plan(
            empresa_id=10,
            plan_code="PLAN_BASE",
            reason="Cambio con sobreconsumo",
            solicitante=self.superadmin,
            ip_address="127.0.0.1"
        )
        self.assertEqual(res.plan, self.plan_base)
        self.assertEqual(res.estado, 'ACTIVO')
        
        # Assert audit code matches overconsumption
        _, kwargs = mock_audit.call_args
        self.assertEqual(kwargs["accion"], "CAMBIO_PLAN_CON_SOBRECONSUMO")

    # 9. API View: GET /api/v1/plans/
    @patch('apps.plans.selectors.plan_selectors.Plan.objects.using')
    def test_api_plan_list(self, mock_plan_using):
        mock_plan_using.return_value.filter.return_value.order_by.return_value = [self.plan_base, self.plan_premium]
        request = self.factory.get('/api/v1/plans/')
        
        from apps.plans.views import PlanListView
        view = PlanListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["codigo"], "PLAN_BASE")

    # 10. API View: GET /api/v1/companies/{emp_id}/plan/
    @patch('apps.plans.views.get_company_active_plan')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin', return_value=False)
    def test_api_company_plan_detail_success(self, mock_superadmin, mock_relation, mock_get_active):
        now = timezone.now()
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base, estado='ACTIVO', fecha_inicio=now - timedelta(days=1), periodicidad='MENSUAL')
        mock_get_active.return_value = ep
        mock_relation.return_value = MagicMock()

        request = self.factory.get('/api/v1/companies/10/plan/')
        force_authenticate(request, user=self.regular_user)
        
        from apps.plans.views import CompanyPlanDetailView
        view = CompanyPlanDetailView.as_view()
        response = view(request, emp_id=10)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["plan"]["codigo"], "PLAN_BASE")

    # 11. API View: GET /api/v1/companies/{emp_id}/plan/usage/
    @patch('apps.plans.views.get_company_active_plan')
    @patch('apps.plans.views.get_company_plan_limits')
    @patch('apps.plans.views.get_company_usage')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.calculate_effective_permissions')
    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin', return_value=False)
    def test_api_company_plan_usage_success(self, mock_superadmin, mock_calc_perms, mock_relation, mock_usage, mock_limits, mock_get_active):
        ep = EmpresaPlan(id=50, empresa=self.company, plan=self.plan_base)
        mock_get_active.return_value = ep
        mock_relation.return_value = MagicMock()
        mock_calc_perms.return_value = {'EMPRESA_VER'}
        
        mock_limits.return_value = {
            "users": 5,
            "editions": 10,
            "storage_bytes": 100 * 1024 * 1024,
            "pdf_mb": 10,
            "paginas_pdf": 10
        }
        mock_usage.return_value = {
            "users": 3,
            "editions": 7,
            "storage_bytes": 40 * 1024 * 1024
        }

        request = self.factory.get('/api/v1/companies/10/plan/usage/')
        force_authenticate(request, user=self.regular_user)
        
        from apps.plans.views import CompanyPlanUsageView
        view = CompanyPlanUsageView.as_view()
        response = view(request, emp_id=10)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"]["limit"], 5)
        self.assertEqual(response.data["users"]["used"], 3)
        self.assertEqual(response.data["users"]["available"], 2)
        
        self.assertEqual(response.data["storage"]["limit_bytes"], 100 * 1024 * 1024)
        self.assertEqual(response.data["storage"]["used_bytes"], 40 * 1024 * 1024)
        self.assertEqual(response.data["storage"]["available_bytes"], 60 * 1024 * 1024)

    # 12. API View: POST /api/v1/companies/{emp_id}/plan/change/ - Forbidden for non-superadmin
    @patch('apps.plans.views.change_company_plan')
    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin', return_value=False)
    def test_api_company_plan_change_forbidden(self, mock_superadmin, mock_change):
        request = self.factory.post('/api/v1/companies/10/plan/change/', {"plan_code": "PLAN_PREMIUM", "reason": "Acceso ilegal"})
        force_authenticate(request, user=self.regular_user)
        
        from apps.plans.views import CompanyPlanChangeView
        view = CompanyPlanChangeView.as_view()
        response = view(request, emp_id=10)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
