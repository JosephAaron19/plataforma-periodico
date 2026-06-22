from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import tempfile
import uuid
import os
from pathlib import Path

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_pagina import EdicionPagina
from apps.access.models.acceso_edicion import AccesoEdicion
from apps.access.models.acceso_tipo import AccesoTipo
from apps.reading.models.sesion_lectura import SesionLectura
from apps.reading.models.progreso_lectura import ProgresoLectura
from apps.files.models.archivo import Archivo

class DummyAtomic:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

@patch('django.db.transaction.atomic', DummyAtomic)
class ReadingSessionViewsTest(SimpleTestCase):
    def setUp(self):
        # Set databases to avoid connection checking errors
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
            razon_social="Empresa Test",
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
            numero_paginas=10,
            estado="PUBLICADA",
            creado_por=self.mock_user,
            eliminado=False
        )

        self.session_id = uuid.uuid4()
        
        self.mock_type = AccesoTipo(id=1, codigo='COMPRA', nombre='Compra', estado='ACTIVO')
        self.mock_access = AccesoEdicion(id=55, usuario=self.mock_user, edicion=self.mock_edition, tipo_acceso=self.mock_type)

        self.mock_session = SesionLectura(
            id=self.session_id,
            usuario=self.mock_user,
            edicion=self.mock_edition,
            acceso=self.mock_access,
            fecha_inicio=timezone.now(),
            pagina_inicio=1,
            pagina_fin=None,
            estado="ACTIVA"
        )

        # Mock reverse relation descriptor
        self.original_paginas_descriptor = Edicion.paginas
        Edicion.paginas = MagicMock()
        self.mock_edition.paginas.filter.return_value.exists.return_value = True

        # Mock save calls
        self.mock_user.save = MagicMock()
        self.mock_company.save = MagicMock()
        self.mock_edition.save = MagicMock()
        self.mock_type.save = MagicMock()
        self.mock_access.save = MagicMock()
        self.mock_session.save = MagicMock()

        # Setup temporary file to simulate stored image
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b"fake image data")
        self.temp_file.close()
        self.temp_file_path = Path(self.temp_file.name)
        
        self.responses_to_close = []

    def tearDown(self):
        Edicion.paginas = self.original_paginas_descriptor

        # Close any open file response handles
        for r in self.responses_to_close:
            try:
                r.close()
            except Exception:
                pass
        
        if os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except Exception:
                pass

    @patch('apps.reading.views.reading_session_views.can_user_read_edition')
    @patch('apps.reading.views.reading_session_views.get_or_create_reading_access')
    @patch('apps.reading.models.sesion_lectura.SesionLectura.objects')
    @patch('apps.editions.models.edicion.Edicion.objects')
    @patch('apps.audit.services.audit_service.AuditService.record_event')
    def test_create_session_success(self, mock_audit, mock_edition_objects, mock_session_objects, mock_get_access, mock_can_read):
        """
        Verify reading session is created successfully when user has access.
        """
        mock_can_read.return_value = True
        mock_edition_objects.using.return_value.select_related.return_value.get.return_value = self.mock_edition
        mock_get_access.return_value = self.mock_access

        mock_session_objects.using.return_value.create.return_value = self.mock_session

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.reading.views.reading_session_views import ReadingSessionCreateView

        factory = APIRequestFactory()
        request = factory.post(f'/api/v1/editions/{self.mock_edition.id}/reading-session/')
        force_authenticate(request, user=self.mock_user)

        view = ReadingSessionCreateView.as_view()
        response = view(request, edi_id=self.mock_edition.id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['session_id'], str(self.session_id))
        mock_audit.assert_called_once()

    @patch('apps.reading.views.reading_session_views.can_user_read_edition')
    @patch('apps.editions.models.edicion.Edicion.objects')
    @patch('apps.audit.services.audit_service.AuditService.record_event')
    def test_create_session_denied(self, mock_audit, mock_edition_objects, mock_can_read):
        """
        Verify reading session creation fails if user has no access rights.
        """
        mock_can_read.return_value = False
        mock_edition_objects.using.return_value.select_related.return_value.get.return_value = self.mock_edition

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.reading.views.reading_session_views import ReadingSessionCreateView

        factory = APIRequestFactory()
        request = factory.post(f'/api/v1/editions/{self.mock_edition.id}/reading-session/')
        force_authenticate(request, user=self.mock_user)

        view = ReadingSessionCreateView.as_view()
        response = view(request, edi_id=self.mock_edition.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_audit.assert_called_once()

    @patch('apps.reading.models.sesion_lectura.SesionLectura.objects')
    @patch('apps.editions.models.edicion_pagina.EdicionPagina.objects')
    @patch('apps.files.services.storage_service.StorageService.get_private_absolute_path')
    @patch('apps.audit.services.audit_service.AuditService.record_event')
    def test_serve_page_success(self, mock_audit, mock_get_path, mock_page_objects, mock_session_objects):
        """
        Verify that a page is served successfully with FileResponse when session is active.
        """
        mock_session_objects.using.return_value.select_related.return_value.get.return_value = self.mock_session
        
        mock_file = Archivo(id=99, ruta_storage="tenant_10/fake.jpg", nombre_original="fake.jpg")
        mock_page = EdicionPagina(id=777, edicion=self.mock_edition, archivo=mock_file, edp_numero_pagina=1, edp_es_actual=True, edp_estado="GENERADA")
        
        mock_page_objects.using.return_value.select_related.return_value.get.return_value = mock_page
        mock_get_path.return_value = self.temp_file_path

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.reading.views.reading_session_views import ReadingSessionPageView

        factory = APIRequestFactory()
        request = factory.get(f'/api/v1/reading-sessions/{self.session_id}/pages/1/')
        force_authenticate(request, user=self.mock_user)

        view = ReadingSessionPageView.as_view()
        response = view(request, session_id=self.session_id, page_number=1)
        self.responses_to_close.append(response)

        self.assertTrue(hasattr(response, 'streaming_content'))
        mock_audit.assert_called_once()

    @patch('apps.reading.models.sesion_lectura.SesionLectura.objects')
    @patch('apps.audit.services.audit_service.AuditService.record_event')
    def test_serve_page_expired_session(self, mock_audit, mock_session_objects):
        """
        Verify serving page fails if session has expired.
        """
        # Set start date to 5 hours ago
        self.mock_session.fecha_inicio = timezone.now() - timedelta(hours=5)
        mock_session_objects.using.return_value.select_related.return_value.get.return_value = self.mock_session
        mock_session_objects.using.return_value.select_for_update.return_value.get.return_value = self.mock_session

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.reading.views.reading_session_views import ReadingSessionPageView

        factory = APIRequestFactory()
        request = factory.get(f'/api/v1/reading-sessions/{self.session_id}/pages/1/')
        force_authenticate(request, user=self.mock_user)

        view = ReadingSessionPageView.as_view()
        response = view(request, session_id=self.session_id, page_number=1)
        self.responses_to_close.append(response)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.mock_session.estado, 'EXPIRADA')
        mock_audit.assert_called_once()

    @patch('apps.reading.models.sesion_lectura.SesionLectura.objects')
    @patch('apps.audit.services.audit_service.AuditService.record_event')
    def test_serve_page_idor_cross_user(self, mock_audit, mock_session_objects):
        """
        Verify serving page fails if session belongs to another user.
        """
        self.mock_session.usuario = Usuario(id=999)
        self.mock_session.usuario_id = 999  # Different user
        mock_session_objects.using.return_value.select_related.return_value.get.return_value = self.mock_session

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.reading.views.reading_session_views import ReadingSessionPageView

        factory = APIRequestFactory()
        request = factory.get(f'/api/v1/reading-sessions/{self.session_id}/pages/1/')
        force_authenticate(request, user=self.mock_user)

        view = ReadingSessionPageView.as_view()
        response = view(request, session_id=self.session_id, page_number=1)
        self.responses_to_close.append(response)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_audit.assert_called_once()

    @patch('apps.reading.models.sesion_lectura.SesionLectura.objects')
    @patch('apps.reading.models.progreso_lectura.ProgresoLectura.objects')
    @patch('apps.audit.services.audit_service.AuditService.record_event')
    def test_progress_tracking_success(self, mock_audit, mock_progress_objects, mock_session_objects):
        """
        Verify that progress is tracked and updated correctly.
        """
        mock_session_objects.using.return_value.select_related.return_value.get.return_value = self.mock_session
        mock_session_objects.using.return_value.select_for_update.return_value.get.return_value = self.mock_session

        mock_progress = ProgresoLectura(id=888, usuario=self.mock_user, edicion=self.mock_edition, ultima_pagina=1)
        mock_progress.save = MagicMock()
        mock_progress_objects.using.return_value.get_or_create.return_value = (mock_progress, False)

        from rest_framework.test import APIRequestFactory, force_authenticate
        from apps.reading.views.reading_session_views import ReadingSessionProgressView

        factory = APIRequestFactory()
        request = factory.post(f'/api/v1/reading-sessions/{self.session_id}/progress/', data={"page_number": 5}, format='json')
        force_authenticate(request, user=self.mock_user)

        view = ReadingSessionProgressView.as_view()
        response = view(request, session_id=self.session_id)
        self.responses_to_close.append(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_progress.ultima_pagina, 5)
        self.assertEqual(mock_progress.porcentaje, 50.00)
        mock_audit.assert_called_once()


@patch('django.db.transaction.atomic', DummyAtomic)
class PublicSampleViewsTest(SimpleTestCase):
    def setUp(self):
        # Set databases to avoid connection checking errors
        self.databases = {'default', 'periodico_db'}

        self.mock_company = Empresa(
            id=10,
            ruc="12345678901",
            razon_social="Empresa Test",
            nombre_comercial="Empresa Test",
            slug="el-tiempo",
            estado="ACTIVA",
            eliminado=False
        )

        self.mock_user = Usuario(id=1, usr_correo="editor@example.com")

        self.mock_edition = Edicion(
            id=100,
            empresa=self.mock_company,
            codigo="E01",
            titulo="Edición Test",
            slug="edicion-1",
            fecha_edicion=timezone.now().date(),
            modalidad="PAGO",
            precio=10.00,
            moneda="PEN",
            numero_paginas=10,
            estado="PUBLICADA",
            creado_por=self.mock_user,
            eliminado=False,
            permite_muestra=True,
            paginas_muestra=3
        )

        # Mock reverse relation descriptor
        self.original_paginas_descriptor = Edicion.paginas
        Edicion.paginas = MagicMock()
        self.mock_edition.paginas.filter.return_value.exists.return_value = True

        # Mock save calls
        self.mock_company.save = MagicMock()
        self.mock_user.save = MagicMock()
        self.mock_edition.save = MagicMock()

        # Setup temporary file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b"fake sample page data")
        self.temp_file.close()
        self.temp_file_path = Path(self.temp_file.name)
        
        self.responses_to_close = []

    def tearDown(self):
        Edicion.paginas = self.original_paginas_descriptor

        for r in self.responses_to_close:
            try:
                r.close()
            except Exception:
                pass
                
        if os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except Exception:
                pass

    @patch('apps.editions.models.edicion.Edicion.objects')
    @patch('apps.editions.models.edicion_pagina.EdicionPagina.objects')
    @patch('apps.files.services.storage_service.StorageService.get_private_absolute_path')
    def test_serve_sample_page_success(self, mock_get_path, mock_page_objects, mock_edition_objects):
        """
        Verify serving sample page within allowed limits returns FileResponse.
        """
        mock_edition_objects.using.return_value.select_related.return_value.get.return_value = self.mock_edition
        
        mock_file = Archivo(id=99, ruta_storage="tenant_10/sample_1.jpg", nombre_original="sample_1.jpg")
        mock_page = EdicionPagina(id=777, edicion=self.mock_edition, archivo=mock_file, edp_numero_pagina=2, edp_es_actual=True, edp_estado="GENERADA")
        mock_page_objects.using.return_value.select_related.return_value.get.return_value = mock_page

        mock_get_path.return_value = self.temp_file_path

        from rest_framework.test import APIRequestFactory
        from apps.reading.views.public_sample_views import PublicSamplePageView

        factory = APIRequestFactory()
        request = factory.get('/api/v1/public/editions/el-tiempo/edicion-1/sample/pages/2/')

        view = PublicSamplePageView.as_view()
        response = view(request, company_slug='el-tiempo', edition_slug='edicion-1', page_number=2)
        self.responses_to_close.append(response)

        self.assertTrue(hasattr(response, 'streaming_content'))

    @patch('apps.editions.models.edicion.Edicion.objects')
    def test_serve_sample_page_out_of_range(self, mock_edition_objects):
        """
        Verify serving sample page out of limits is rejected with 403 Forbidden.
        """
        mock_edition_objects.using.return_value.select_related.return_value.get.return_value = self.mock_edition

        from rest_framework.test import APIRequestFactory
        from apps.reading.views.public_sample_views import PublicSamplePageView

        factory = APIRequestFactory()
        # Page 4 requested but allows max 3
        request = factory.get('/api/v1/public/editions/el-tiempo/edicion-1/sample/pages/4/')

        view = PublicSamplePageView.as_view()
        response = view(request, company_slug='el-tiempo', edition_slug='edicion-1', page_number=4)
        self.responses_to_close.append(response)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
