from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from rest_framework import serializers
from rest_framework.test import APIRequestFactory, force_authenticate
import datetime

# Models
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.companies.models.empresa_identidad import EmpresaIdentidad
from apps.companies.models.empresa_configuracion import EmpresaConfiguracion
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.rol import Rol
from apps.plans.models.plan import Plan
from apps.plans.models.empresa_plan import EmpresaPlan
from apps.files.models.archivo import Archivo

# Selectors
from apps.companies.selectors.company_selectors import (
    get_all_companies_for_admin,
    get_authorized_companies_for_user,
    get_company_active_plan
)
from apps.companies.selectors.company_file_selectors import validate_company_file_reference

# Services
from apps.companies.services.company_create_service import create_company
from apps.companies.services.company_update_service import update_company
from apps.companies.services.company_identity_service import update_company_identity
from apps.companies.services.company_configuration_service import update_company_configuration

# Serializers
from apps.companies.serializers.company_create import CompanyCreateSerializer
from apps.companies.serializers.company_detail import CompanyDetailSerializer
from apps.companies.serializers.company_update import CompanyUpdateSerializer
from apps.companies.serializers.company_identity import CompanyIdentitySerializer
from apps.companies.serializers.company_configuration import CompanyConfigurationSerializer

# Views
from apps.companies.views.companies import CompanyListCreateView, CompanyDetailUpdateView


@contextmanager
def dummy_atomic(using=None, savepoint=True):
    yield


class CompanySelectorsTest(SimpleTestCase):
    """
    Test case for company and file selectors.
    """
    @patch('apps.companies.models.empresa.Empresa.objects.filter')
    def test_get_all_companies_for_admin(self, mock_filter):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        
        res = get_all_companies_for_admin()
        mock_filter.assert_called_once_with(eliminado=False)
        self.assertEqual(res, mock_qs.select_related.return_value.prefetch_related.return_value)

    @patch('apps.companies.models.empresa.Empresa.objects.filter')
    def test_get_authorized_companies_for_user(self, mock_filter):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        mock_user = Usuario(id=2)
        
        res = get_authorized_companies_for_user(mock_user)
        mock_filter.assert_called_once_with(
            eliminado=False,
            usuario_empresas__usuario=mock_user,
            usuario_empresas__estado='ACTIVO'
        )
        self.assertEqual(
            res, 
            mock_qs.select_related.return_value.prefetch_related.return_value.distinct.return_value
        )

    @patch('apps.plans.models.empresa_plan.EmpresaPlan.objects.filter')
    def test_get_company_active_plan(self, mock_filter):
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs
        
        get_company_active_plan(12)
        mock_filter.assert_called_once_with(empresa_id=12, estado='ACTIVO')

    @patch('apps.files.models.archivo.Archivo.objects.get')
    def test_validate_company_file_reference_valid(self, mock_get):
        mock_file = Archivo(id=100)
        mock_file.empresa_id = 5
        mock_file.estado = 'DISPONIBLE'
        mock_file.eliminado = False
        mock_get.return_value = mock_file
        
        self.assertTrue(validate_company_file_reference(100, 5))
        mock_get.assert_called_once_with(id=100)

    @patch('apps.files.models.archivo.Archivo.objects.get')
    def test_validate_company_file_reference_invalid_company(self, mock_get):
        mock_file = Archivo(id=100)
        mock_file.empresa_id = 99  # different company
        mock_file.estado = 'DISPONIBLE'
        mock_file.eliminado = False
        mock_get.return_value = mock_file
        
        self.assertFalse(validate_company_file_reference(100, 5))

    @patch('apps.files.models.archivo.Archivo.objects.get')
    def test_validate_company_file_reference_deleted_or_unavailable(self, mock_get):
        mock_file = Archivo(id=100)
        mock_file.empresa_id = 5
        mock_file.estado = 'ELIMINADO'
        mock_file.eliminado = True
        mock_get.return_value = mock_file
        
        self.assertFalse(validate_company_file_reference(100, 5))

    @patch('apps.files.models.archivo.Archivo.objects.get')
    def test_validate_company_file_reference_not_found(self, mock_get):
        mock_get.side_effect = Archivo.DoesNotExist
        self.assertFalse(validate_company_file_reference(100, 5))


class CompanyCreateServiceTest(SimpleTestCase):
    """
    Test case for transactional company creation service.
    """
    def setUp(self):
        self.superadmin = Usuario(
            id=1,
            usr_correo="super@example.com",
            nombres="Super",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False
        )
        
        self.admin_user = Usuario(
            id=2,
            usr_correo="admin@example.com",
            nombres="Admin",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False,
            bloqueado_hasta=None
        )

    @patch('apps.companies.services.company_create_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.companies.services.company_create_service.AuditService.record_event')
    @patch('apps.companies.services.company_create_service.EmpresaHistorial.save')
    @patch('apps.companies.services.company_create_service.EmpresaPlan.save')
    @patch('apps.companies.services.company_create_service.UsuarioEmpresaRol.save')
    @patch('apps.companies.services.company_create_service.UsuarioEmpresa.save')
    @patch('apps.companies.services.company_create_service.EmpresaConfiguracion.save')
    @patch('apps.companies.services.company_create_service.EmpresaIdentidad.save')
    @patch('apps.companies.services.company_create_service.Empresa.save')
    @patch('apps.companies.services.company_create_service.Empresa.objects.using')
    @patch('apps.companies.services.company_create_service.Plan.objects.using')
    @patch('apps.companies.services.company_create_service.Rol.objects.using')
    @patch('apps.companies.services.company_create_service.Usuario.objects.using')
    def test_create_company_success(
        self, mock_user_using, mock_rol_using, mock_plan_using, mock_empresa_using,
        mock_empresa_save, mock_identidad_save, mock_config_save, mock_ue_save,
        mock_uer_save, mock_ep_save, mock_historial_save, mock_audit, mock_atomic
    ):
        # Setup mocks for resolution
        mock_user_using.return_value.get.return_value = self.admin_user
        
        mock_rol = Rol(codigo='ADMIN_EMPRESA', estado='ACTIVO')
        mock_rol_using.return_value.get.return_value = mock_rol
        
        mock_plan = Plan(
            codigo='PLAN_BASE',
            estado='ACTIVO',
            precio=10.00,
            moneda='PEN',
            periodicidad='MENSUAL'
        )
        mock_plan_using.return_value.get.return_value = mock_plan
        
        # Empresa filter mock (not exist check)
        mock_emp_qs = MagicMock()
        mock_emp_qs.filter.return_value.exists.return_value = False
        mock_empresa_using.return_value = mock_emp_qs

        # Run creation
        company = create_company(
            ruc='10203040506',
            razon_social='Demo S.A.',
            nombre_comercial='Demo Corp',
            slug='demo-corp',
            creado_por=self.superadmin,
            administrator_user_id=2,
            descripcion='Test company'
        )
        
        self.assertEqual(company.ruc, '10203040506')
        self.assertEqual(company.razon_social, 'Demo S.A.')
        self.assertEqual(company.creado_por, self.superadmin)
        self.assertEqual(company.estado, 'PENDIENTE')
        
        # Verify save calls
        mock_empresa_save.assert_called_once()
        mock_identidad_save.assert_called_once()
        mock_config_save.assert_called_once()
        mock_ue_save.assert_called_once()
        mock_uer_save.assert_called_once()
        mock_ep_save.assert_called_once()
        mock_historial_save.assert_called_once()
        mock_audit.assert_called_once()

    @patch('apps.companies.services.company_create_service.Usuario.objects.using')
    def test_create_company_admin_user_not_found(self, mock_user_using):
        mock_user_using.return_value.get.side_effect = Usuario.DoesNotExist
        
        with self.assertRaises(ValidationError) as ctx:
            create_company(
                ruc='10203040506',
                razon_social='Demo S.A.',
                nombre_comercial='Demo Corp',
                slug='demo-corp',
                creado_por=self.superadmin,
                administrator_user_id=999
            )
        self.assertIn("administrator_user_id", ctx.exception.message_dict)

    @patch('apps.companies.services.company_create_service.Usuario.objects.using')
    def test_create_company_admin_user_inactive_or_blocked(self, mock_user_using):
        # Case: Inactive
        inactive_user = Usuario(
            id=2,
            estado='PENDIENTE',
            eliminado=False
        )
        mock_user_using.return_value.get.return_value = inactive_user
        
        with self.assertRaises(ValidationError):
            create_company(
                ruc='10203040506',
                razon_social='Demo S.A.',
                nombre_comercial='Demo Corp',
                slug='demo-corp',
                creado_por=self.superadmin,
                administrator_user_id=2
            )


class CompanyUpdateServiceTest(SimpleTestCase):
    """
    Test case for updating company information.
    """
    @patch('apps.companies.services.company_update_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.companies.services.company_update_service.AuditService.record_event')
    @patch('apps.companies.services.company_update_service.EmpresaHistorial.save')
    @patch('apps.companies.services.company_update_service.Empresa.save')
    def test_update_company_success(self, mock_save, mock_historial_save, mock_audit, mock_atomic):
        company = Empresa(
            id=5,
            ruc='10203040506',
            razon_social='Old Name S.A.',
            nombre_comercial='Old Corp',
            slug='old-corp',
            estado='PENDIENTE'
        )
        user = Usuario(id=1)
        
        updated_company = update_company(
            empresa=company,
            actualizado_por=user,
            razon_social='New Name S.A.',
            nombre_comercial='New Corp'
        )
        
        self.assertEqual(updated_company.razon_social, 'New Name S.A.')
        self.assertEqual(updated_company.nombre_comercial, 'New Corp')
        mock_save.assert_called_once()
        mock_historial_save.assert_called_once()
        mock_audit.assert_called_once()


class CompanyIdentityServiceTest(SimpleTestCase):
    """
    Test case for updating company identity visual details.
    """
    @patch('apps.companies.services.company_identity_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.companies.services.company_identity_service.AuditService.record_event')
    @patch('apps.companies.services.company_identity_service.EmpresaHistorial.save')
    @patch('apps.companies.services.company_identity_service.validate_company_file_reference')
    @patch('apps.companies.services.company_identity_service.EmpresaIdentidad.save')
    def test_update_company_identity_success(
        self, mock_save, mock_file_val, mock_historial_save, mock_audit, mock_atomic
    ):
        company = Empresa(id=5)
        identidad = EmpresaIdentidad(empresa=company, nombre_publico='Old Pub', estado='BORRADOR')
        company.identidad = identidad
        
        mock_file_val.return_value = True  # valid file
        user = Usuario(id=1)
        
        updated_identidad = update_company_identity(
            empresa=company,
            actualizado_por=user,
            nombre_publico='New Pub',
            logo_archivo_id=123
        )
        
        self.assertEqual(updated_identidad.nombre_publico, 'New Pub')
        self.assertEqual(updated_identidad.logo_archivo_id, 123)
        self.assertEqual(updated_identidad.estado, 'ACTIVO')
        mock_save.assert_called_once()
        mock_historial_save.assert_called_once()
        mock_audit.assert_called_once()

    @patch('apps.companies.services.company_identity_service.validate_company_file_reference')
    def test_update_company_identity_invalid_file(self, mock_file_val):
        company = Empresa(id=5)
        identidad = EmpresaIdentidad(empresa=company, nombre_publico='Old Pub', estado='BORRADOR')
        company.identidad = identidad
        
        mock_file_val.return_value = False  # invalid file reference
        user = Usuario(id=1)
        
        with self.assertRaises(ValidationError) as ctx:
            update_company_identity(
                empresa=company,
                actualizado_por=user,
                logo_archivo_id=999
            )
        self.assertIn("logo_archivo_id", ctx.exception.message_dict)


class CompanyConfigurationServiceTest(SimpleTestCase):
    """
    Test case for updating company configurations.
    """
    @patch('apps.companies.services.company_configuration_service.transaction.atomic', side_effect=dummy_atomic)
    @patch('apps.companies.services.company_configuration_service.AuditService.record_event')
    @patch('apps.companies.services.company_configuration_service.EmpresaHistorial.save')
    @patch('apps.companies.services.company_configuration_service.EmpresaConfiguracion.save')
    def test_update_company_configuration_success(
        self, mock_save, mock_historial_save, mock_audit, mock_atomic
    ):
        company = Empresa(id=5)
        config = EmpresaConfiguracion(empresa=company, moneda='PEN', idioma='es')
        company.configuracion = config
        user = Usuario(id=1)
        
        # Test whitelisted modification
        updated_config = update_company_configuration(
            empresa=company,
            actualizado_por=user,
            config_data={
                'moneda': 'USD',
                'idioma': 'en',
                'limite_pdf_mb': 500  # not whitelisted/sensitive, should be ignored
            }
        )
        
        self.assertEqual(updated_config.moneda, 'USD')
        self.assertEqual(updated_config.idioma, 'en')
        self.assertEqual(updated_config.limite_pdf_mb, 50)  # default, untouched
        mock_save.assert_called_once()
        mock_historial_save.assert_called_once()
        mock_audit.assert_called_once()


class CompanySerializersTest(SimpleTestCase):
    """
    Test case for serializers and their validation logic.
    """
    def test_company_update_serializer_ignores_immutable_fields(self):
        data = {
            'ruc': '99999999999',  # immutable
            'slug': 'new-slug',     # immutable
            'estado': 'ACTIVO',     # immutable
            'razon_social': 'Mutable Name S.A.'
        }
        # Enforce partial=True so required model fields that are omitted don't fail validation
        serializer = CompanyUpdateSerializer(data=data, partial=True)
        serializer.is_valid()
        
        # Verify immutable fields are not captured in validated_data
        self.assertNotIn('ruc', serializer.validated_data)
        self.assertNotIn('slug', serializer.validated_data)
        self.assertNotIn('estado', serializer.validated_data)
        self.assertEqual(serializer.validated_data['razon_social'], 'Mutable Name S.A.')


class CompanyViewsPermissionsTest(SimpleTestCase):
    """
    Test case to verify views and permission gating with mocks.
    """
    def setUp(self):
        self.factory = APIRequestFactory()
        
        self.superadmin = Usuario(
            id=1,
            usr_correo="super@example.com",
            nombres="Super",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False
        )

        self.normal_user = Usuario(
            id=2,
            usr_correo="normal@example.com",
            nombres="Normal",
            estado="ACTIVO",
            correo_verificado=True,
            eliminado=False
        )

    @patch('apps.companies.views.companies.is_platform_superadmin')
    @patch('apps.companies.views.companies.get_all_companies_for_admin')
    def test_company_list_superadmin(self, mock_get_all, mock_is_superadmin):
        mock_is_superadmin.return_value = True
        mock_get_all.return_value = Empresa.objects.none()
        
        request = self.factory.get('/api/v1/companies/')
        force_authenticate(request, user=self.superadmin)
        
        view = CompanyListCreateView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        mock_get_all.assert_called_once()

    @patch('apps.companies.views.companies.is_platform_superadmin')
    @patch('apps.companies.views.companies.get_authorized_companies_for_user')
    def test_company_list_normal_user(self, mock_get_auth, mock_is_superadmin):
        mock_is_superadmin.return_value = False
        mock_get_auth.return_value = Empresa.objects.none()
        
        request = self.factory.get('/api/v1/companies/')
        force_authenticate(request, user=self.normal_user)
        
        view = CompanyListCreateView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 200)
        mock_get_auth.assert_called_once_with(self.normal_user)

    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin')
    def test_company_create_permission_denied_for_normal_user(self, mock_is_superadmin):
        mock_is_superadmin.return_value = False
        
        request = self.factory.post('/api/v1/companies/', {})
        force_authenticate(request, user=self.normal_user)
        
        view = CompanyListCreateView.as_view()
        response = view(request)
        
        self.assertEqual(response.status_code, 403)
