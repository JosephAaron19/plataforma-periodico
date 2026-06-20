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
from apps.configuration.selectors.parametro_selectors import get_system_parameter_value
from apps.processing.exceptions import TransientProcessingError

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

    # Keep track of physical files generated to clean up on failures/cancellation
    generated_files = []
    doc = None
    es_publico_portada = True
    
    # We will process, catching errors to store in database
    try:
        edition = procesamiento.edicion
        company_id = edition.empresa_id
        pdf_file_association = procesamiento.archivo_edicion
        original_pdf = pdf_file_association.archivo

        pdf_abs_path = StorageService.get_private_absolute_path(original_pdf.ruta_storage)

        if not os.path.exists(pdf_abs_path):
            raise FileNotFoundError(f"Archivo PDF original no encontrado en la ruta {pdf_abs_path}")

        # Open doc using PyMuPDF inside try-finally to close safely
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

        # 2. Extract and render pages
        paginas_muestra = edition.paginas_muestra or 0
        permite_muestra = edition.permite_muestra
        paginas_generadas = 0
        pages_to_create = []

        for page_idx in range(page_count):
            # Check for cooperative cancellation request in each iteration
            try:
                proc_check = Procesamiento.objects.using('periodico_db').get(id=procesamiento.id)
                if proc_check.estado == 'CANCELADO':
                    logger.info(f"Procesamiento {procesamiento.id} cancelado cooperativamente en iteracion.")
                    # Clean up any files generated in this run
                    for path in generated_files:
                        StorageService.delete_private_file(path)
                    return False
            except Exception as check_err:
                print("CANCELLATION CHECK ERROR:", str(check_err), type(check_err))
                logger.warning(f"Error checking cancellation status: {str(check_err)}")

            page = doc.load_page(page_idx)
            
            # Enforce maximum resolution (DPI capped at 150)
            pix = page.get_pixmap(dpi=150)
            img_data = pix.tobytes("jpeg")

            # Check image dimensions (ancho <= 3000 px, alto <= 4000 px)
            if pix.width > 3000 or pix.height > 4000:
                raise ValidationError(
                    f"La imagen generada para la página {page_idx + 1} excede las dimensiones máximas permitidas (3000x4000 px). Tiene {pix.width}x{pix.height} px.",
                    code='EXCEDE_DIMENSIONES_IMAGEN'
                )

            # Check image file size (<= 5 MB)
            if len(img_data) > 5 * 1024 * 1024:
                raise ValidationError(
                    f"El tamaño de la imagen generada para la página {page_idx + 1} ({len(img_data) / (1024*1024):.2f} MB) excede el límite de 5 MB.",
                    code='EXCEDE_TAMANO_IMAGEN'
                )

            # Pages are ALWAYS stored in private storage.
            # No exposure under media root or public url.
            content_file = ContentFile(img_data, name=f"page_{page_idx + 1}.jpg")
            saved_path = StorageService.save_private_file(content_file, company_id, f"page_{page_idx + 1}.jpg")
            generated_files.append(saved_path)

            hash_sha256 = hashlib.sha256(img_data).hexdigest()
            es_muestra = permite_muestra and (page_idx + 1) <= paginas_muestra

            # Save page metadata to write atomically at the end
            pages_to_create.append({
                "saved_path": saved_path,
                "size": len(img_data),
                "hash": hash_sha256,
                "width": pix.width,
                "height": pix.height,
                "es_muestra": es_muestra
            })

            # Update progress monotonically in DB
            paginas_generadas += 1
            with transaction.atomic(using='periodico_db'):
                procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=procesamiento.id)
                procesamiento.total_paginas_generadas = paginas_generadas
                procesamiento.porcentaje_avance = Decimal(paginas_generadas) / Decimal(page_count) * Decimal(100)
                procesamiento.save(using='periodico_db')

        # 3. Render and save cover (PORTADA) from page 0
        first_page = doc.load_page(0)
        pix_cover = first_page.get_pixmap(dpi=150)
        cover_data = pix_cover.tobytes("jpeg")

        # Validate cover resource limits
        if pix_cover.width > 3000 or pix_cover.height > 4000:
            raise ValidationError(
                "La imagen de portada generada excede las dimensiones máximas permitidas (3000x4000 px).",
                code='EXCEDE_DIMENSIONES_IMAGEN'
            )
        if len(cover_data) > 5 * 1024 * 1024:
            raise ValidationError(
                "El tamaño de la imagen de portada generada excede el límite permitido de 5 MB.",
                code='EXCEDE_TAMANO_IMAGEN'
            )

        # Retrieve cover publicity policy from system configuration
        es_publico_portada = get_system_parameter_value('PERMITIR_PORTADA_PUBLICA', True)
        
        cover_file = ContentFile(cover_data, name="cover.jpg")
        if es_publico_portada:
            saved_cover_path = StorageService.save_public_file(cover_file, company_id, "cover.jpg")
        else:
            saved_cover_path = StorageService.save_private_file(cover_file, company_id, "cover.jpg")
            
        generated_files.append(saved_cover_path)
        hash_cover = hashlib.sha256(cover_data).hexdigest()

        # 4. Final atomic database transaction
        with transaction.atomic(using='periodico_db'):
            # Deactivate and replace previous page records atomically
            EdicionPagina.objects.using('periodico_db').filter(
                edicion=edition,
                edp_es_actual=True
            ).update(
                edp_es_actual=False,
                edp_estado='REEMPLAZADA',
                edp_fecha_invalidacion=timezone.now(),
                edp_motivo_invalidacion='Reemplazada por nuevo procesamiento'
            )

            # Deactivate previous cover records atomically
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

                old_cov_file = old_cov.archivo
                old_cov_file.estado = 'REEMPLAZADO'
                old_cov_file.save(using='periodico_db')

            # Create Archivo and EdicionPagina records for all pages
            for idx, pdata in enumerate(pages_to_create):
                archivo_pag = Archivo.objects.using('periodico_db').create(
                    empresa_id=company_id,
                    creado_por=procesamiento.solicitado_por,
                    nombre_original=f"page_{idx + 1}.jpg",
                    nombre_interno=os.path.basename(pdata["saved_path"]),
                    extension='jpg',
                    tipo_mime='image/jpeg',
                    tamano_bytes=pdata["size"],
                    hash_sha256=pdata["hash"],
                    ruta_storage=pdata["saved_path"],
                    proveedor_storage='LOCAL',
                    contenedor='private',
                    es_publico=False,
                    version=1,
                    estado='DISPONIBLE',
                    eliminado=False
                )

                EdicionPagina.objects.using('periodico_db').create(
                    edicion=edition,
                    intento=intento,
                    archivo=archivo_pag,
                    edp_numero_pagina=idx + 1,
                    edp_ancho_px=pdata["width"],
                    edp_alto_px=pdata["height"],
                    edp_tamano_bytes=pdata["size"],
                    edp_hash_sha256=pdata["hash"],
                    edp_es_muestra=pdata["es_muestra"],
                    edp_es_actual=True,
                    edp_estado='GENERADA',
                    edp_fecha_generacion=timezone.now()
                )

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
                contenedor='public' if es_publico_portada else 'private',
                es_publico=es_publico_portada,
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
            procesamiento.porcentaje_avance = Decimal(100)
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

        # Clean up any physical files generated during this run to avoid orphans
        for path in generated_files:
            try:
                # Page files are always private, but cover could be public
                if "cover.jpg" in path and es_publico_portada:
                    StorageService.delete_public_file(path)
                else:
                    StorageService.delete_private_file(path)
            except Exception as clean_err:
                logger.error(f"Error deleting temp file {path}: {str(clean_err)}")

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

        is_transient = category not in ['VALIDACION', 'LECTURA_PDF']

        # Save failure details to DB
        with transaction.atomic(using='periodico_db'):
            # Reload
            intento = ProcesamientoIntento.objects.using('periodico_db').select_for_update().get(id=intento_id)
            procesamiento = Procesamiento.objects.using('periodico_db').select_for_update().get(id=intento.procesamiento_id)
            
            # Fetch retry limit and count existing attempts
            max_retries = int(get_system_parameter_value('MAX_REINTENTOS_PROCESAMIENTO', 3))
            attempts_count = ProcesamientoIntento.objects.using('periodico_db').filter(procesamiento=procesamiento).count()
            
            should_retry = is_transient and (attempts_count <= max_retries)

            # Update attempt state
            intento.pri_estado = 'ERROR'
            intento.pri_resultado = 'FALLIDO'
            intento.pri_reintentable = should_retry
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
                pre_reintentable=should_retry,
                pre_severidad='ERROR',
                pre_fecha=timezone.now()
            )

            if should_retry:
                # Create a new ProcesamientoIntento in CREADO for next Celery task run
                new_intento = ProcesamientoIntento.objects.using('periodico_db').create(
                    procesamiento=procesamiento,
                    pri_numero_intento=attempts_count + 1,
                    pri_estado='CREADO',
                    pri_solicitado_por=intento.pri_solicitado_por,
                    edi_id=intento.edi_id
                )
                
                # Keep parent Processing in PROCESANDO / PENDIENTE status, do not transition edition yet
                procesamiento.estado = 'PROCESANDO'
                procesamiento.resultado_resumen = f"Intento {intento.pri_numero_intento} fallido. Encolando reintento {new_intento.pri_numero_intento}..."
                procesamiento.save(using='periodico_db')
                
                # Throw custom TransientProcessingError to bubble up to Celery task
                raise TransientProcessingError(new_intento.id, attempts_count, exc)

            else:
                # Exhausted attempts or logical error
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

        return False

    finally:
        # Safe closing of PyMuPDF document
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
