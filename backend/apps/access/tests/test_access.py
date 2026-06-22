from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import json

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.access.models.acceso_tipo import AccesoTipo
from apps.access.services.access_service import can_user_read_edition, get_or_create_reading_access

class DummyAtomic:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

@patch('django.db.transaction.atomic', DummyAtomic)
class AccessServiceTest(SimpleTestCase):
    def setUp(self):
        self.databases = {'default', 'periodico_db'}

        self.mock_user = Usuario(
            id=1,
            usr_correo="user@example.com",
            nombres="John",
            apellidos="Doe",
            estado="ACTIVO",
            correo_verificado=True
        )

        self.mock_company = Empresa(
            id=10,
            ruc="12345678901",
            razon_social="Empresa Test S.A.C.",
            nombre_comercial="Empresa Test",
            slug="empresa-test",
            estado="ACTIVA",
            eliminado=False
        )

        self.mock_edition = Edicion(
            id=100,
            empresa=self.mock_company,
            codigo="E01",
            titulo="Edición Test",
            slug="edicion-test",
            fecha_edicion=timezone.now().date(),
            modalidad="PAGO",
            precio=10.00,
            moneda="PEN",
            numero_paginas=20,
            estado="PUBLICADA",
            creado_por=self.mock_user,
            eliminado=False
        )

        # Mock reverse relation by overriding class attribute temporarily
        self.original_paginas_descriptor = Edicion.paginas
        Edicion.paginas = MagicMock()

        # Mock save methods
        self.mock_user.save = MagicMock()
        self.mock_company.save = MagicMock()
        self.mock_edition.save = MagicMock()

        # Start permission service patcher
        self.calc_perms_patcher = patch('apps.access.services.access_service.calculate_effective_permissions')
        self.mock_calc_perms = self.calc_perms_patcher.start()
        self.mock_calc_perms.return_value = set()

    def tearDown(self):
        self.calc_perms_patcher.stop()
        Edicion.paginas = self.original_paginas_descriptor

    def test_can_user_read_edition_free(self):
        """
        Verify that user can read a free edition without explicit access records.
        """
        self.mock_edition.modalidad = 'GRATUITA'
        # Mock that pages exist
        self.mock_edition.paginas.filter.return_value.exists.return_value = True

        res = can_user_read_edition(self.mock_user, self.mock_edition)
        self.assertTrue(res)

    def test_can_user_read_edition_no_pages(self):
        """
        Verify that reading is denied if there are no processed pages available.
        """
        self.mock_edition.modalidad = 'GRATUITA'
        self.mock_edition.paginas.filter.return_value.exists.return_value = False

        res = can_user_read_edition(self.mock_user, self.mock_edition)
        self.assertFalse(res)

    @patch('apps.access.models.acceso_edicion.AccesoEdicion.objects')
    def test_can_user_read_edition_with_active_access(self, mock_access_objects):
        """
        Verify that reading is allowed if the user has an active AccesoEdicion record.
        """
        self.mock_edition.paginas.filter.return_value.exists.return_value = True
        
        # Mock active access exists
        mock_qs = mock_access_objects.using.return_value.filter.return_value.filter.return_value
        mock_qs.exists.return_value = True

        res = can_user_read_edition(self.mock_user, self.mock_edition)
        self.assertTrue(res)

    @patch('apps.access.models.acceso_edicion.AccesoEdicion.objects')
    def test_can_user_read_edition_with_company_permission(self, mock_access_objects):
        """
        Verify that reading is allowed if the user has EDICION_VER permission in the company.
        """
        self.mock_edition.paginas.filter.return_value.exists.return_value = True
        
        # Mock active access does NOT exist
        mock_qs = mock_access_objects.using.return_value.filter.return_value.filter.return_value
        mock_qs.exists.return_value = False

        # Mock permission EDICION_VER exists
        self.mock_calc_perms.return_value = {'EDICION_VER'}

        res = can_user_read_edition(self.mock_user, self.mock_edition)
        self.assertTrue(res)

    @patch('apps.access.models.acceso_edicion.AccesoEdicion.objects')
    def test_can_user_read_edition_denied(self, mock_access_objects):
        """
        Verify that reading is denied if user has no access, no permissions, and edition is not free.
        """
        self.mock_edition.paginas.filter.return_value.exists.return_value = True
        mock_qs = mock_access_objects.using.return_value.filter.return_value.filter.return_value
        mock_qs.exists.return_value = False
        self.mock_calc_perms.return_value = set()

        res = can_user_read_edition(self.mock_user, self.mock_edition)
        self.assertFalse(res)

    @patch('apps.access.models.acceso_tipo.AccesoTipo.objects')
    @patch('apps.access.models.acceso_edicion.AccesoEdicion.objects')
    def test_get_or_create_reading_access_free_edition(self, mock_access_objects, mock_type_objects):
        """
        Verify that a free access is automatically created if the edition is free.
        """
        self.mock_edition.modalidad = 'GRATUITA'
        
        # Mock no existing access
        mock_filter_qs = mock_access_objects.using.return_value.filter.return_value.filter.return_value
        mock_filter_qs.first.return_value = None

        mock_type_gratuito = AccesoTipo(id=2, codigo='GRATUITO', nombre='Gratuito', estado='ACTIVO')
        mock_type_objects.using.return_value.get.return_value = mock_type_gratuito

        mock_created_access = AccesoEdicion(id=1, usuario=self.mock_user, edicion=self.mock_edition, tipo_acceso=mock_type_gratuito)
        mock_access_objects.using.return_value.get_or_create.return_value = (mock_created_access, True)

        access = get_or_create_reading_access(self.mock_user, self.mock_edition)
        self.assertEqual(access, mock_created_access)


@patch('django.db.transaction.atomic', DummyAtomic)
@patch('apps.access.views.library_views.is_platform_superadmin')
@patch('apps.access.models.acceso_edicion.AccesoEdicion.objects')
@patch('apps.editions.models.edicion.Edicion.objects')
class LibraryListViewTest(SimpleTestCase):
    def setUp(self):
        self.databases = {'default', 'periodico_db'}

        self.mock_user = Usuario(
            id=1,
            usr_correo="user@example.com",
            nombres="John",
            apellidos="Doe",
            estado="ACTIVO",
            correo_verificado=True
        )

        # Global patchers for auth selectors/permissions to avoid DB query hits
        self.get_companies_patcher = patch('apps.access.views.library_views.get_active_user_companies')
        self.mock_get_companies = self.get_companies_patcher.start()
        self.mock_get_companies.return_value = []

        self.calc_perms_patcher = patch('apps.access.views.library_views.calculate_effective_permissions')
        self.mock_calc_perms = self.calc_perms_patcher.start()
        self.mock_calc_perms.return_value = set()

    def tearDown(self):
        self.get_companies_patcher.stop()
        self.calc_perms_patcher.stop()

    def test_library_empty(self, mock_edition_objects, mock_access_objects, mock_is_super):
        """
        Verify library returns empty list if no editions are accessible.
        """
        mock_is_super.return_value = False
        
        # Mock active accesses to be empty
        mock_access_qs = mock_access_objects.using.return_value.filter.return_value.filter.return_value
        mock_access_qs.values_list.return_value = []

        # Mock edition listing returning empty queryset
        mock_edition_qs = mock_edition_objects.using.return_value.select_related.return_value.filter.return_value.filter.return_value
        mock_edition_qs.distinct.return_value.order_by.return_value = []

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.access.views.library_views import LibraryListView

        factory = APIRequestFactory()
        request = factory.get('/api/v1/library/')
        force_authenticate(request, user=self.mock_user)

        view = LibraryListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_library_with_accesses(self, mock_edition_objects, mock_access_objects, mock_is_super):
        """
        Verify library returns accessible editions.
        """
        mock_is_super.return_value = False
        self.mock_get_companies.return_value = []
        
        # Mock active accesses returning edition ID 100
        mock_access_qs = mock_access_objects.using.return_value.filter.return_value.filter.return_value
        mock_access_qs.values_list.return_value = [100]

        mock_company = Empresa(
            id=10,
            ruc="12345678901",
            razon_social="Empresa Test",
            nombre_comercial="Empresa Test",
            slug="empresa-test",
            estado="ACTIVA",
            eliminado=False
        )

        mock_edition = Edicion(
            id=100,
            empresa=mock_company,
            codigo='E01',
            titulo='Edición Test',
            slug='edicion-test',
            fecha_edicion=timezone.now().date(),
            fecha_publicacion=timezone.now(),
            modalidad='PAGO',
            precio=10.00,
            moneda='PEN',
            numero_paginas=20,
            es_destacada=False,
            permite_muestra=False,
            paginas_muestra=None
        )

        mock_edition_qs = mock_edition_objects.using.return_value.select_related.return_value.filter.return_value.filter.return_value
        mock_edition_qs.distinct.return_value.order_by.return_value = [mock_edition]

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.access.views.library_views import LibraryListView

        factory = APIRequestFactory()
        request = factory.get('/api/v1/library/')
        force_authenticate(request, user=self.mock_user)

        view = LibraryListView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], 100)
        self.assertEqual(response.data[0]['titulo'], 'Edición Test')
