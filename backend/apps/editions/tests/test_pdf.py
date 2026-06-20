import os
import hashlib
from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import MagicMock, patch
from datetime import timedelta
from contextlib import contextmanager
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_archivo import EdicionArchivo
from apps.files.models.archivo import Archivo
from apps.processing.models.procesamiento import Procesamiento
from apps.processing.models.procesamiento_intento import ProcesamientoIntento
from apps.processing.models.procesamiento_error import ProcesamientoError
from apps.editions.models.edicion_pagina import EdicionPagina
from apps.editions.constants import EstadoEdicion

@contextmanager
def dummy_atomic(*args, **kwargs):
    yield

class PDFUploadAndProcessingTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        
        self.editor = Usuario(id=2, usr_correo="editor@ejemplo.com", nombres="Editor", apellidos="User", estado="ACTIVO", correo_verificado=True)
        self.company = Empresa(id=10, razon_social="Empresa Test", ruc="20123456789", slug="empresa-test", estado="ACTIVA", eliminado=False)
        self.edition = Edicion(
            id=100,
            empresa=self.company,
            codigo="EDI-001",
            titulo="Edición Especial",
            slug="edicion-especial",
            fecha_edicion=timezone.now().date(),
            modalidad="PAGO",
            precio=10.00,
            moneda="PEN",
            estado=EstadoEdicion.BORRADOR,
            creado_por=self.editor,
            eliminado=False
        )
        
        # Mock active plan
        self.mock_plan = MagicMock()
        self.mock_plan.limite_pdf_mb = 10
        self.mock_plan.limite_paginas_pdf = 20
        self.mock_plan_relation = MagicMock()
        self.mock_plan_relation.plan = self.mock_plan
        
        # Setup common patches
        self.patcher_atomic = patch('django.db.transaction.atomic', side_effect=dummy_atomic)
        self.patcher_on_commit = patch('django.db.transaction.on_commit')
        self.patcher_audit = patch('apps.audit.services.audit_service.AuditService.record_event')
        
        # Patch all save methods to prevent DB queries in SimpleTestCase
        self.patcher_ed_save = patch('apps.editions.models.edicion.Edicion.save')
        self.patcher_arc_save = patch('apps.files.models.archivo.Archivo.save')
        self.patcher_eda_save = patch('apps.editions.models.edicion_archivo.EdicionArchivo.save')
        self.patcher_pro_save = patch('apps.processing.models.procesamiento.Procesamiento.save')
        self.patcher_pri_save = patch('apps.processing.models.procesamiento_intento.ProcesamientoIntento.save')
        self.patcher_pre_save = patch('apps.processing.models.procesamiento_error.ProcesamientoError.save')
        self.patcher_hist_save = patch('apps.editions.models.edicion_historial.EdicionHistorial.save')
        self.patcher_edp_save = patch('apps.editions.models.edicion_pagina.EdicionPagina.save')

        self.mock_atomic = self.patcher_atomic.start()
        self.mock_on_commit = self.patcher_on_commit.start()
        self.mock_audit = self.patcher_audit.start()
        
        self.patcher_ed_save.start()
        self.patcher_arc_save.start()
        self.patcher_eda_save.start()
        self.patcher_pro_save.start()
        self.patcher_pri_save.start()
        self.patcher_pre_save.start()
        self.patcher_hist_save.start()
        self.patcher_edp_save.start()

    def tearDown(self):
        patch.stopall()

    # --- SERVICE TESTS (upload_edition_pdf) ---

    @patch('apps.files.services.pdf_upload_service.get_company_active_plan')
    @patch('apps.files.services.pdf_upload_service.check_storage_limit')
    @patch('apps.files.services.pdf_upload_service.fitz.open')
    @patch('apps.files.services.pdf_upload_service.StorageService.save_private_file')
    @patch('apps.files.services.pdf_upload_service.Empresa.objects.using')
    @patch('apps.files.services.pdf_upload_service.Edicion.objects.using')
    @patch('apps.files.services.pdf_upload_service.EdicionArchivo.objects.using')
    @patch('apps.files.services.pdf_upload_service.Archivo.objects.using')
    @patch('apps.files.services.pdf_upload_service.Procesamiento.objects.using')
    @patch('apps.files.services.pdf_upload_service.ProcesamientoIntento.objects.using')
    @patch('apps.files.services.pdf_upload_service.EdicionHistorial.objects.using')
    def test_upload_pdf_success(
        self, mock_hist_using, mock_intento_using, mock_proc_using, mock_arc_using, 
        mock_eda_using, mock_edi_using, mock_emp_using, mock_save_file, mock_fitz, 
        mock_storage_limit, mock_get_plan
    ):
        mock_get_plan.return_value = self.mock_plan_relation
        mock_storage_limit.return_value = {"allowed": True}
        
        # Mock fitz document
        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.page_count = 5
        mock_fitz.return_value = mock_doc
        
        mock_save_file.return_value = "tenant_10/abc-123.pdf"
        
        # Mock db queries
        mock_emp_using.return_value.select_for_update.return_value.get.return_value = self.company
        mock_edi_using.return_value.select_for_update.return_value.get.return_value = self.edition
        mock_eda_using.return_value.filter.return_value = []
        
        pdf_file = SimpleUploadedFile("test.pdf", b"%PDF-1.4\n%...\n", content_type="application/pdf")
        
        from apps.files.services.pdf_upload_service import upload_edition_pdf
        res = upload_edition_pdf(
            company_id=10,
            edition_id=100,
            user=self.editor,
            uploaded_file=pdf_file,
            ip_address="127.0.0.1"
        )
        
        self.assertEqual(res.estado, EstadoEdicion.PENDIENTE_PROCESAMIENTO)
        mock_save_file.assert_called_once()
        self.mock_on_commit.assert_called_once()

    @patch('apps.files.services.pdf_upload_service.fitz.open')
    def test_upload_pdf_invalid_signature(self, mock_fitz):
        pdf_file = SimpleUploadedFile("test.pdf", b"NOTAPDF", content_type="application/pdf")
        
        from apps.files.services.pdf_upload_service import upload_edition_pdf
        with self.assertRaises(ValidationError) as ctx:
            upload_edition_pdf(
                company_id=10,
                edition_id=100,
                user=self.editor,
                uploaded_file=pdf_file
            )
        self.assertIn("firma mágica inválida", str(ctx.exception))
        mock_fitz.assert_not_called()

    @patch('apps.files.services.pdf_upload_service.fitz.open')
    def test_upload_pdf_encrypted(self, mock_fitz):
        mock_doc = MagicMock()
        mock_doc.is_encrypted = True
        mock_fitz.return_value = mock_doc
        
        pdf_file = SimpleUploadedFile("test.pdf", b"%PDF-1.4\n", content_type="application/pdf")
        
        from apps.files.services.pdf_upload_service import upload_edition_pdf
        with self.assertRaises(ValidationError) as ctx:
            upload_edition_pdf(
                company_id=10,
                edition_id=100,
                user=self.editor,
                uploaded_file=pdf_file
            )
        self.assertIn("está encriptado o protegido con contraseña", str(ctx.exception))

    @patch('apps.files.services.pdf_upload_service.get_company_active_plan')
    @patch('apps.files.services.pdf_upload_service.fitz.open')
    @patch('apps.files.services.pdf_upload_service.Empresa.objects.using')
    @patch('apps.files.services.pdf_upload_service.Edicion.objects.using')
    def test_upload_pdf_size_limit_exceeded(self, mock_edi_using, mock_emp_using, mock_fitz, mock_get_plan):
        self.mock_plan.limite_pdf_mb = 1  # 1MB limit
        mock_get_plan.return_value = self.mock_plan_relation
        
        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.page_count = 5
        mock_fitz.return_value = mock_doc
        
        mock_emp_using.return_value.select_for_update.return_value.get.return_value = self.company
        mock_edi_using.return_value.select_for_update.return_value.get.return_value = self.edition
        
        # 2MB file size
        pdf_file = SimpleUploadedFile("test.pdf", b"%PDF-1.4\n" + b" " * (2 * 1024 * 1024), content_type="application/pdf")
        
        from apps.files.services.pdf_upload_service import upload_edition_pdf
        with self.assertRaises(ValidationError) as ctx:
            upload_edition_pdf(
                company_id=10,
                edition_id=100,
                user=self.editor,
                uploaded_file=pdf_file
            )
        self.assertIn("excede el límite permitido por el plan", str(ctx.exception))

    # --- PROCESSOR TESTS (process_pdf_attempt) ---

    @patch('apps.processing.services.pdf_processor.get_company_active_plan')
    @patch('apps.processing.services.pdf_processor.fitz.open')
    @patch('apps.processing.services.pdf_processor.StorageService.get_private_absolute_path')
    @patch('apps.processing.services.pdf_processor.StorageService.save_public_file')
    @patch('apps.processing.services.pdf_processor.StorageService.save_private_file')
    @patch('apps.processing.services.pdf_processor.ProcesamientoIntento.objects.using')
    @patch('apps.processing.services.pdf_processor.Procesamiento.objects.using')
    @patch('apps.processing.services.pdf_processor.EdicionPagina.objects.using')
    @patch('apps.processing.services.pdf_processor.Archivo.objects.using')
    @patch('apps.processing.services.pdf_processor.EdicionArchivo.objects.using')
    @patch('apps.processing.services.pdf_processor.Edicion.objects.using')
    @patch('apps.processing.services.pdf_processor.EdicionHistorial.objects.using')
    @patch('apps.processing.services.pdf_processor.os.path.exists', return_value=True)
    def test_process_pdf_success(
        self, mock_exists, mock_hist_using, mock_edi_using, mock_eda_using, mock_arc_using, 
        mock_pag_using, mock_proc_using, mock_intento_using, mock_save_private, mock_save_public, 
        mock_abs_path, mock_fitz, mock_get_plan
    ):
        mock_get_plan.return_value = self.mock_plan_relation
        
        # Setup models
        pdf_archivo = Archivo(id=888, ruta_storage="tenant_10/abc.pdf", estado="CARGANDO", tamano_bytes=1000)
        eda = EdicionArchivo(id=999, archivo=pdf_archivo, tipo_archivo="PDF_ORIGINAL", es_actual=True, empresa=self.company)
        proc = Procesamiento(id=1, edicion=self.edition, archivo_edicion=eda, estado='PENDIENTE', es_actual=True, solicitado_por=self.editor)
        intento = ProcesamientoIntento(id=5, procesamiento=proc, pri_estado='CREADO', pri_numero_intento=1, pri_solicitado_por=self.editor)
        
        mock_intento_using.return_value.select_for_update.return_value.get.return_value = intento
        mock_proc_using.return_value.select_for_update.return_value.get.return_value = proc
        
        # Mock fitz document pages
        mock_doc = MagicMock()
        mock_doc.page_count = 2
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.width = 1000
        mock_pix.height = 1400
        mock_pix.tobytes.return_value = b"imagedata"
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_fitz.return_value = mock_doc
        
        mock_save_private.return_value = "tenant_10/page1.jpg"
        mock_save_public.return_value = "tenant_10/cover.jpg"
        
        from apps.processing.services.pdf_processor import process_pdf_attempt
        res = process_pdf_attempt(intento_id=5)
        
        self.assertTrue(res)
        self.assertEqual(intento.pri_estado, 'COMPLETADO')
        self.assertEqual(proc.estado, 'COMPLETADO')
        self.assertEqual(self.edition.estado, EstadoEdicion.PROCESADA)

    @patch('apps.processing.services.pdf_processor.get_company_active_plan')
    @patch('apps.processing.services.pdf_processor.fitz.open')
    @patch('apps.processing.services.pdf_processor.StorageService.get_private_absolute_path')
    @patch('apps.processing.services.pdf_processor.ProcesamientoIntento.objects.using')
    @patch('apps.processing.services.pdf_processor.Procesamiento.objects.using')
    @patch('apps.processing.services.pdf_processor.ProcesamientoError.objects.using')
    @patch('apps.processing.services.pdf_processor.Edicion.objects.using')
    @patch('apps.processing.services.pdf_processor.EdicionHistorial.objects.using')
    @patch('apps.processing.services.pdf_processor.os.path.exists', return_value=True)
    def test_process_pdf_pages_limit_exceeded(
        self, mock_exists, mock_hist_using, mock_edi_using, mock_error_using, mock_proc_using, 
        mock_intento_using, mock_abs_path, mock_fitz, mock_get_plan
    ):
        self.mock_plan.limite_paginas_pdf = 2  # Plan limit is 2 pages
        mock_get_plan.return_value = self.mock_plan_relation
        
        pdf_archivo = Archivo(id=888, ruta_storage="tenant_10/abc.pdf", estado="CARGANDO", tamano_bytes=1000)
        eda = EdicionArchivo(id=999, archivo=pdf_archivo, tipo_archivo="PDF_ORIGINAL", es_actual=True, empresa=self.company)
        proc = Procesamiento(id=1, edicion=self.edition, archivo_edicion=eda, estado='PENDIENTE', es_actual=True, solicitado_por=self.editor)
        intento = ProcesamientoIntento(id=5, procesamiento=proc, pri_estado='CREADO', pri_numero_intento=1, pri_solicitado_por=self.editor)
        
        mock_intento_using.return_value.select_for_update.return_value.get.return_value = intento
        mock_proc_using.return_value.select_for_update.return_value.get.return_value = proc
        mock_edi_using.return_value.select_for_update.return_value.get.return_value = self.edition
        
        # PDF has 5 pages (exceeds limit!)
        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_fitz.return_value = mock_doc
        
        from apps.processing.services.pdf_processor import process_pdf_attempt
        res = process_pdf_attempt(intento_id=5)
        
        self.assertFalse(res)
        self.assertEqual(intento.pri_estado, 'ERROR')
        self.assertEqual(proc.estado, 'ERROR')
        self.assertEqual(self.edition.estado, EstadoEdicion.ERROR)
        mock_error_using.return_value.create.assert_called_once()
        
        _, kwargs = mock_error_using.return_value.create.call_args
        self.assertEqual(kwargs["pre_codigo"], 'LIMITE_PAGINAS_EXCEDIDO')

    # --- VIEW TESTS ---

    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin', return_value=False)
    @patch('apps.authorization.permissions.drf_permissions.calculate_effective_permissions')
    def test_upload_pdf_view_permission_denied(self, mock_calc_perms, mock_superadmin, mock_relation):
        mock_relation.return_value = MagicMock()
        # User lacks EDICION_EDITAR permission
        mock_calc_perms.return_value = {'EDICION_VER'}
        
        request = self.factory.post('/api/v1/companies/10/editions/100/pdf/', {"file": "dummy"})
        force_authenticate(request, user=self.editor)
        
        from apps.editions.views.pdf_views import CompanyEditionPDFView
        view = CompanyEditionPDFView.as_view()
        response = view(request, emp_id=10, edi_id=100)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.editions.views.pdf_views.get_company_edition_by_id')
    @patch('apps.editions.views.pdf_views.EdicionArchivo.objects.using')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin', return_value=False)
    @patch('apps.authorization.permissions.drf_permissions.calculate_effective_permissions')
    def test_get_pdf_metadata_success(self, mock_calc_perms, mock_superadmin, mock_relation, mock_eda_using, mock_get_edition):
        mock_relation.return_value = MagicMock()
        mock_calc_perms.return_value = {'EDICION_EDITAR'}
        mock_get_edition.return_value = self.edition
        
        archivo = Archivo(
            id=200, nombre_original="original.pdf", extension="pdf",
            tipo_mime="application/pdf", tamano_bytes=5000, hash_sha256="hashsha",
            ruta_storage="tenant_10/internal.pdf", es_publico=False, estado="DISPONIBLE"
        )
        eda = EdicionArchivo(id=300, edicion=self.edition, archivo=archivo, tipo_archivo='PDF_ORIGINAL', es_actual=True)
        mock_eda_using.return_value.filter.return_value.select_related.return_value.first.return_value = eda
        
        request = self.factory.get('/api/v1/companies/10/editions/100/pdf/')
        force_authenticate(request, user=self.editor)
        
        from apps.editions.views.pdf_views import CompanyEditionPDFView
        view = CompanyEditionPDFView.as_view()
        response = view(request, emp_id=10, edi_id=100)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert storage path is not exposed in the response
        self.assertNotIn("ruta_storage", response.data)
        self.assertNotIn("internal.pdf", str(response.data))
        self.assertEqual(response.data["nombre_original"], "original.pdf")

    @patch('apps.editions.views.pdf_views.get_company_edition_by_id')
    @patch('apps.editions.views.pdf_views.Procesamiento.objects.using')
    @patch('apps.processing.serializers.processing_serializers.ProcesamientoError.objects.using')
    @patch('apps.authorization.permissions.drf_permissions.get_user_company_relation')
    @patch('apps.authorization.permissions.drf_permissions.is_platform_superadmin', return_value=False)
    @patch('apps.authorization.permissions.drf_permissions.calculate_effective_permissions')
    def test_get_processing_status_success(self, mock_calc_perms, mock_superadmin, mock_relation, mock_error_using, mock_proc_using, mock_get_edition):
        mock_relation.return_value = MagicMock()
        mock_calc_perms.return_value = {'PROCESAMIENTO_VER'}
        mock_get_edition.return_value = self.edition
        
        proc = Procesamiento(
            id=1, version=1, estado='PROCESANDO', total_paginas_esperadas=10,
            total_paginas_generadas=3, porcentaje_avance=30.00,
            fecha_solicitud=timezone.now()
        )
        mock_proc_using.return_value.filter.return_value.first.return_value = proc
        mock_error_using.return_value.filter.return_value.order_by.return_value = []
        
        request = self.factory.get('/api/v1/companies/10/editions/100/processing/')
        force_authenticate(request, user=self.editor)
        
        from apps.editions.views.pdf_views import CompanyEditionProcessingStatusView
        view = CompanyEditionProcessingStatusView.as_view()
        response = view(request, emp_id=10, edi_id=100)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "PROCESANDO")
        self.assertEqual(float(response.data["porcentaje_avance"]), 30.00)
