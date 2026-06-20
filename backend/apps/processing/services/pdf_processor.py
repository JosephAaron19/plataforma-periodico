import os
import hashlib
import fitz
import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

from apps.editions.constants import EstadoEdicion, EventoEdicionHistorial
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_archivo import EdicionArchivo
from apps.editions.models.edicion_historial import EdicionHistorial
from apps.editions.models.edicion_pagina import EdicionPagina
from apps.files.models.archivo import Archivo
from apps.files.services.storage_service import StorageService
from apps.processing.models.procesamiento import Procesamiento
from apps.processing.models.procesamiento_intento import ProcesamientoIntento
from apps.processing.models.procesamiento_error import ProcesamientoError
from apps.plans.selectors.plan_selectors import get_company_active_plan
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaAccion, AuditoriaModulo, AuditoriaResultado

logger = logging.getLogger(__name__)

def process_pdf_attempt(intento_id: int) -> bool:
    """
    Core function that processes the PDF for a specific attempt.
    Extracts pages, generates page images, cover, updates states and registers errors/audits.
    """
    # 1. Idempotency: Lock the attempt and check its state
    with transaction.atomic(using='periodico_db'):
        try:
            intento = ProcesamientoIntento.objects.using('periodico_db').select_for_update().get(id=intento_id)
        except ProcesamientoIntento.DoesNotExist:
            logger.error(f"Intento {intento_id} no encontrado en base de datos.")
            return False

        if intento.pri_estado not in ['CREADO', 'EN_COLA']:
            logger.info(f"Intento {intento_id} ya esta en estado {intento.pri_estado}. Omitiendo ejecucion.")
            return True

        # Lock the parent processing record
        try:
            procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=intento.procesamiento_id)
        except Procesamiento.DoesNotExist:
            logger.error(f"Procesamiento {intento.procesamiento_id} no encontrado.")
            return False

        # Transition to EJECUTANDO
        intento.pri_estado = 'EJECUTANDO'
        intento.pri_fecha_inicio = timezone.now()
        intento.save(using='periodico_db')

        procesamiento.estado = 'PROCESANDO'
        procesamiento.fecha_inicio = timezone.now()
        procesamiento.save(using='periodico_db')

    # Now we process, catching errors to store in database
    try:
        edition = procesamiento.edicion
        company_id = edition.empresa_id
        pdf_file_association = procesamiento.archivo_edicion
        original_pdf = pdf_file_association.archivo

        pdf_abs_path = StorageService.get_private_absolute_path(original_pdf.ruta_storage)

        if not os.path.exists(pdf_abs_path):
            raise FileNotFoundError(f"Archivo PDF original no encontrado en la ruta {pdf_abs_path}")

        # Open doc using PyMuPDF
        doc = fitz.open(pdf_abs_path)
        page_count = doc.page_count

        with transaction.atomic(using='periodico_db'):
            # Reload locked records to be safe
            procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=procesamiento.id)
            procesamiento.total_paginas_esperadas = page_count
            procesamiento.save(using='periodico_db')

            # Plan check for pages count
            active_plan_relation = get_company_active_plan(company_id)
            if not active_plan_relation:
                raise ValidationError("La empresa no tiene un plan activo asignado.")

            plan = active_plan_relation.plan
            limite_paginas = plan.limite_paginas_pdf

            if limite_paginas is not None and page_count > limite_paginas:
                # Page limit exceeded
                raise ValidationError(
                    f"El archivo PDF contiene {page_count} páginas, excediendo el límite de su plan ({limite_paginas} páginas).",
                    code='LIMITE_PAGINAS_EXCEDIDO'
                )

        # Deactivate old page records if they exist
        with transaction.atomic(using='periodico_db'):
            EdicionPagina.objects.using('periodico_db').filter(
                edicion=edition,
                edp_es_actual=True
            ).update(edp_es_actual=False, edp_estado='REEMPLAZADA', edp_fecha_invalidacion=timezone.now(), edp_motivo_invalidacion='Reemplazada por nuevo procesamiento')

        # 2. Extract and render pages
        paginas_muestra = edition.paginas_muestra or 0
        permite_muestra = edition.permite_muestra
        paginas_generadas = 0

        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            # Render page at 150 DPI for standard resolution
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("jpeg")

            # Determine sample page and publicity settings
            es_muestra = permite_muestra and (page_idx + 1) <= paginas_muestra
            es_publico = es_muestra

            content_file = ContentFile(img_data, name=f"page_{page_idx + 1}.jpg")

            # Save file using StorageService
            if es_publico:
                saved_path = StorageService.save_public_file(content_file, company_id, f"page_{page_idx + 1}.jpg")
            else:
                saved_path = StorageService.save_private_file(content_file, company_id, f"page_{page_idx + 1}.jpg")

            hash_sha256 = hashlib.sha256(img_data).hexdigest()

            with transaction.atomic(using='periodico_db'):
                # Save Archivo record
                archivo_pag = Archivo.objects.using('periodico_db').create(
                    empresa_id=company_id,
                    creado_por=procesamiento.solicitado_por,
                    nombre_original=f"page_{page_idx + 1}.jpg",
                    nombre_interno=os.path.basename(saved_path),
                    extension='jpg',
                    tipo_mime='image/jpeg',
                    tamano_bytes=len(img_data),
                    hash_sha256=hash_sha256,
                    ruta_storage=saved_path,
                    proveedor_storage='LOCAL',
                    contenedor='public' if es_publico else 'private',
                    es_publico=es_publico,
                    version=1,
                    estado='DISPONIBLE',
                    eliminado=False
                )

                # Save EdicionPagina record
                EdicionPagina.objects.using('periodico_db').create(
                    edicion=edition,
                    intento=intento,
                    archivo=archivo_pag,
                    edp_numero_pagina=page_idx + 1,
                    edp_ancho_px=pix.width,
                    edp_alto_px=pix.height,
                    edp_tamano_bytes=len(img_data),
                    edp_hash_sha256=hash_sha256,
                    edp_es_muestra=es_muestra,
                    edp_es_actual=True,
                    edp_estado='GENERADA',
                    edp_fecha_generacion=timezone.now()
                )

                paginas_generadas += 1

                # Update processing progress monotonically
                procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=procesamiento.id)
                procesamiento.total_paginas_generadas = paginas_generadas
                procesamiento.porcentaje_avance = Decimal(paginas_generadas) / Decimal(page_count) * Decimal(100)
                procesamiento.save(using='periodico_db')

        # 3. Render and save cover (PORTADA) from page 0
        first_page = doc.load_page(0)
        pix_cover = first_page.get_pixmap(dpi=150)
        cover_data = pix_cover.tobytes("jpeg")

        cover_file = ContentFile(cover_data, name="cover.jpg")
        # Cover is always public
        saved_cover_path = StorageService.save_public_file(cover_file, company_id, "cover.jpg")
        hash_cover = hashlib.sha256(cover_data).hexdigest()

        with transaction.atomic(using='periodico_db'):
            # Deactivate previous cover records if exist
            old_covers = EdicionArchivo.objects.using('periodico_db').filter(
                edicion=edition,
                tipo_archivo='PORTADA',
                es_actual=True
            )
            for old_cov in old_covers:
                old_cov.es_actual = False
                old_cov.estado = 'REEMPLAZADO'
                old_cov.fecha_reemplazo = timezone.now()
                old_cov.motivo_reemplazo = 'Reemplazado por nuevo procesamiento'
                old_cov.save(using='periodico_db')

                # Update previous cover file state
                old_cov_file = old_cov.archivo
                old_cov_file.estado = 'REEMPLAZADO'
                old_cov_file.save(using='periodico_db')

            # Create Archivo for cover
            archivo_cover = Archivo.objects.using('periodico_db').create(
                empresa_id=company_id,
                creado_por=procesamiento.solicitado_por,
                nombre_original="cover.jpg",
                nombre_interno=os.path.basename(saved_cover_path),
                extension='jpg',
                tipo_mime='image/jpeg',
                tamano_bytes=len(cover_data),
                hash_sha256=hash_cover,
                ruta_storage=saved_cover_path,
                proveedor_storage='LOCAL',
                contenedor='public',
                es_publico=True,
                version=1,
                estado='DISPONIBLE',
                eliminado=False
            )

            # Create EdicionArchivo association for cover
            EdicionArchivo.objects.using('periodico_db').create(
                edicion=edition,
                archivo=archivo_cover,
                tipo_archivo='PORTADA',
                version=1,
                es_actual=True,
                estado='ACTIVO',
                asignado_por=procesamiento.solicitado_por,
                empresa_id=company_id
            )

            # Set original PDF to DISPONIBLE
            original_pdf.estado = 'DISPONIBLE'
            original_pdf.save(using='periodico_db')

            # Update attempts and processing status to successful
            intento = ProcesamientoIntento.objects.using('periodico_db').select_for_update().get(id=intento.id)
            intento.pri_estado = 'COMPLETADO'
            intento.pri_resultado = 'EXITOSO'
            intento.pri_fecha_fin = timezone.now()
            intento.pri_duracion_segundos = int((intento.pri_fecha_fin - intento.pri_fecha_inicio).total_seconds())
            intento.pri_paginas_generadas = paginas_generadas
            intento.save(using='periodico_db')

            procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=procesamiento.id)
            procesamiento.estado = 'COMPLETADO'
            procesamiento.resultado_resumen = f"Procesamiento completado exitosamente. {paginas_generadas} páginas generadas."
            procesamiento.fecha_fin = timezone.now()
            procesamiento.save(using='periodico_db')

            # Update edition state
            old_edition_estado = edition.estado
            edition.estado = EstadoEdicion.PROCESADA
            edition.numero_paginas = paginas_generadas
            edition.save(using='periodico_db')

            # Create history record
            EdicionHistorial.objects.using('periodico_db').create(
                edicion=edition,
                tipo_evento=EventoEdicionHistorial.PROCESAMIENTO_COMPLETADO,
                estado_anterior=old_edition_estado,
                estado_nuevo=EstadoEdicion.PROCESADA,
                valores_anteriores={"estado": old_edition_estado},
                valores_nuevos={
                    "estado": EstadoEdicion.PROCESADA,
                    "paginas_generadas": paginas_generadas
                },
                realizado_por=procesamiento.solicitado_por,
                resultado='EXITOSO'
            )

            # Record audit event
            AuditService.record_event(
                usuario=procesamiento.solicitado_por,
                emp_id=company_id,
                modulo=AuditoriaModulo.M05,
                accion=AuditoriaAccion.PROCESAMIENTO_COMPLETADO,
                entidad="Edicion",
                entidad_id=str(edition.id),
                valores_nuevos={
                    "estado": EstadoEdicion.PROCESADA,
                    "paginas_generadas": paginas_generadas
                },
                resultado=AuditoriaResultado.EXITOSO
            )

        return True

    except Exception as exc:
        logger.exception(f"Error procesando el PDF en intento {intento_id}")

        # Classify the error category
        category = 'DESCONOCIDO'
        code = 'PROCESAMIENTO_FALLIDO'
        user_msg = "Ocurrió un error inesperado al procesar el archivo PDF."
        tech_msg = str(exc)

        if isinstance(exc, ValidationError):
            category = 'VALIDACION'
            code = getattr(exc, 'code', 'VALIDACION_FALLIDA')
            user_msg = exc.message
        elif isinstance(exc, FileNotFoundError):
            category = 'ALMACENAMIENTO'
            code = 'ARCHIVO_NO_ENCONTRADO'
            user_msg = "No se pudo localizar el archivo PDF cargado."
        elif isinstance(exc, fitz.FileDataError):
            category = 'LECTURA_PDF'
            code = 'LECTURA_PDF_FALLIDA'
            user_msg = "El formato del PDF es inválido o está corrupto."

        # Save failure details to DB
        with transaction.atomic(using='periodico_db'):
            # Reload
            intento = ProcesamientoIntento.objects.using('periodico_db').select_for_update().get(id=intento_id)
            intento.pri_estado = 'ERROR'
            intento.pri_resultado = 'FALLIDO'
            intento.pri_fecha_fin = timezone.now()
            if intento.pri_fecha_inicio:
                intento.pri_duracion_segundos = int((intento.pri_fecha_fin - intento.pri_fecha_inicio).total_seconds())
            intento.save(using='periodico_db')

            # Create ProcesamientoError
            ProcesamientoError.objects.using('periodico_db').create(
                intento=intento,
                pre_codigo=code,
                pre_categoria=category,
                pre_mensaje_usuario=user_msg[:500],
                pre_mensaje_tecnico=tech_msg,
                pre_reintentable=False if category in ['VALIDACION', 'LECTURA_PDF'] else True,
                pre_severidad='ERROR',
                pre_fecha=timezone.now()
            )

            # Update parent processing status
            procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=procesamiento.id)
            procesamiento.estado = 'ERROR'
            procesamiento.resultado_resumen = f"Error: {user_msg}"
            procesamiento.fecha_fin = timezone.now()
            procesamiento.save(using='periodico_db')

            # Update edition state
            edition = Edicion.objects.using('periodico_db').select_for_update().get(id=procesamiento.edicion.id)
            old_edition_estado = edition.estado
            edition.estado = EstadoEdicion.ERROR
            edition.save(using='periodico_db')

            # Create history record
            EdicionHistorial.objects.using('periodico_db').create(
                edicion=edition,
                tipo_evento=EventoEdicionHistorial.PROCESAMIENTO_ERROR,
                estado_anterior=old_edition_estado,
                estado_nuevo=EstadoEdicion.ERROR,
                valores_anteriores={"estado": old_edition_estado},
                valores_nuevos={
                    "estado": EstadoEdicion.ERROR,
                    "error_codigo": code
                },
                realizado_por=procesamiento.solicitado_por,
                resultado='ERROR'
            )

            # Record audit event
            AuditService.record_event(
                usuario=procesamiento.solicitado_por,
                emp_id=edition.empresa_id,
                modulo=AuditoriaModulo.M05,
                accion=AuditoriaAccion.PROCESAMIENTO_FALLIDO,
                entidad="Edicion",
                entidad_id=str(edition.id),
                valores_nuevos={
                    "estado": EstadoEdicion.ERROR,
                    "error_codigo": code
                },
                resultado=AuditoriaResultado.ERROR,
                motivo=user_msg
            )

        # Bubble up if it is a transient error to trigger celery retry
        if category not in ['VALIDACION', 'LECTURA_PDF']:
            raise exc

        return False
