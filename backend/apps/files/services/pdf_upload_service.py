import os
import hashlib
import fitz
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_archivo import EdicionArchivo
from apps.editions.models.edicion_historial import EdicionHistorial
from apps.editions.constants import EstadoEdicion, EventoEdicionHistorial
from apps.files.models.archivo import Archivo
from apps.files.services.storage_service import StorageService
from apps.processing.models.procesamiento import Procesamiento
from apps.processing.models.procesamiento_intento import ProcesamientoIntento
from apps.plans.selectors.plan_selectors import get_company_active_plan
from apps.plans.services.plan_limit_service import check_storage_limit
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaAccion, AuditoriaModulo, AuditoriaResultado

def upload_edition_pdf(
    *,
    company_id: int,
    edition_id: int,
    user: Usuario,
    uploaded_file,
    ip_address: str = None,
    user_agent: str = None
) -> Edicion:
    """
    Validates and uploads the main PDF file for an edition following a strict safety order:
    1. Validate file (magic bytes, structure, encryption, page count, dimensions).
    2. Save physically to private storage.
    3. Start database transaction and lock company & edition rows.
    4. Validate plan and storage limits.
    5. Register file in database, associate with edition, and create processing records.
    6. Transition edition state.
    7. Commit transaction and enqueue Celery task.
    
    If database operations fail, the physical file is deleted.
    """
    # 1. Validate file signature and content
    uploaded_file.seek(0)
    header = uploaded_file.read(4)
    uploaded_file.seek(0)

    if header != b'%PDF':
        raise ValidationError("El archivo no es un PDF válido (firma mágica inválida).")

    file_size = uploaded_file.size

    # Open PDF with PyMuPDF to validate layout and structures
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        uploaded_file.seek(0)
    except Exception as e:
        uploaded_file.seek(0)
        raise ValidationError(f"No se pudo leer el archivo PDF. Podría estar corrupto o incompleto. Detalle: {str(e)}")

    try:
        if doc.is_encrypted:
            raise ValidationError("El archivo PDF está encriptado o protegido con contraseña.")
        
        page_count = doc.page_count
        if page_count <= 0:
            raise ValidationError("El archivo PDF no contiene páginas.")

        # Validate reasonable dimensions for each page (max 5000 pt, min 100 pt)
        for page_idx in range(page_count):
            try:
                page = doc.load_page(page_idx)
                rect = page.rect
                width, height = rect.width, rect.height
                if width < 100 or height < 100 or width > 5000 or height > 5000:
                    raise ValidationError(
                        f"La página {page_idx + 1} tiene dimensiones fuera de rango permitido ({width:.1f}x{height:.1f} pt)."
                    )
            except Exception as pe:
                if isinstance(pe, ValidationError):
                    raise pe
                raise ValidationError(f"Error al analizar la estructura de la página {page_idx + 1}. Documento corrupto.")
    finally:
        doc.close()

    # 2. Save physically to private storage
    relative_path = None
    try:
        # Generate sha256 checksum
        uploaded_file.seek(0)
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        hash_sha256 = hasher.hexdigest()
        uploaded_file.seek(0)

        # Save private file
        relative_path = StorageService.save_private_file(uploaded_file, company_id, uploaded_file.name)
    except Exception as io_err:
        raise ValidationError(f"Error de almacenamiento físico del archivo. Detalle: {str(io_err)}")

    # 3. Start database transaction
    try:
        with transaction.atomic(using='periodico_db'):
            # 4. Lock company and edition rows
            try:
                company = Empresa.objects.using('periodico_db').select_for_update().get(id=company_id, eliminado=False)
            except Empresa.DoesNotExist:
                raise ValidationError("La empresa especificada no existe o fue eliminada.")

            if company.estado != 'ACTIVA':
                raise ValidationError("La empresa no está activa.")

            try:
                edition = Edicion.objects.using('periodico_db').select_for_update().get(
                    id=edition_id,
                    empresa_id=company_id,
                    eliminado=False
                )
            except Edicion.DoesNotExist:
                raise ValidationError("La edición especificada no existe o fue eliminada.")

            # Check allowed state (BORRADOR or ERROR)
            if edition.estado not in [EstadoEdicion.BORRADOR, EstadoEdicion.ERROR]:
                raise ValidationError(
                    f"No se puede subir un PDF para esta edición en su estado actual ({edition.estado}). "
                    "Debe estar en BORRADOR o ERROR."
                )

            # 5. Check plan limits
            active_plan_relation = get_company_active_plan(company_id)
            if not active_plan_relation:
                raise ValidationError("La empresa no tiene un plan activo asignado.")

            plan = active_plan_relation.plan
            
            # Check PDF size limit
            limite_pdf_mb = plan.limite_pdf_mb
            if limite_pdf_mb is not None:
                max_bytes = limite_pdf_mb * 1024 * 1024
                if file_size > max_bytes:
                    raise ValidationError(
                        f"El tamaño del archivo ({file_size / (1024 * 1024):.2f} MB) excede el límite permitido por el plan ({limite_pdf_mb} MB)."
                    )

            # Check total storage limit
            storage_check = check_storage_limit(company_id, additional_bytes=file_size)
            if not storage_check["allowed"]:
                raise ValidationError(storage_check["message"])

            # 6. Deactivate old PDF and derived associations (PORTADA, etc.)
            old_ed_files = EdicionArchivo.objects.using('periodico_db').filter(
                edicion=edition,
                tipo_archivo__in=['PDF_ORIGINAL', 'PORTADA', 'MINIATURA', 'PREVIEW'],
                es_actual=True
            )
            for old_eda in old_ed_files:
                old_eda.es_actual = False
                old_eda.estado = 'REEMPLAZADO'
                old_eda.fecha_reemplazo = timezone.now()
                old_eda.motivo_reemplazo = 'Reemplazado por carga de nuevo PDF'
                old_eda.save(using='periodico_db')
                
                old_file = old_eda.archivo
                old_file.estado = 'REEMPLAZADO'
                old_file.save(using='periodico_db')

            # 7. Create Archivo record
            ext = os.path.splitext(uploaded_file.name)[1].lower() or '.pdf'
            archivo = Archivo.objects.using('periodico_db').create(
                empresa=company,
                creado_por=user,
                nombre_original=uploaded_file.name,
                nombre_interno=os.path.basename(relative_path),
                extension=ext.replace('.', ''),
                tipo_mime='application/pdf',
                tamano_bytes=file_size,
                hash_sha256=hash_sha256,
                ruta_storage=relative_path,
                proveedor_storage='LOCAL',
                contenedor='private',
                es_publico=False,
                version=1,
                estado='CARGANDO',
                eliminado=False
            )

            # 8. Create EdicionArchivo association
            edicion_archivo = EdicionArchivo.objects.using('periodico_db').create(
                edicion=edition,
                archivo=archivo,
                tipo_archivo='PDF_ORIGINAL',
                version=1,
                es_actual=True,
                estado='ACTIVO',
                asignado_por=user,
                empresa=company
            )

            # Deactivate previous processings
            Procesamiento.objects.using('periodico_db').filter(
                edicion=edition,
                es_actual=True
            ).update(es_actual=False)

            version_proc = Procesamiento.objects.using('periodico_db').filter(edicion=edition).count() + 1

            # 9. Create Procesamiento record
            procesamiento = Procesamiento.objects.using('periodico_db').create(
                edicion=edition,
                archivo_edicion=edicion_archivo,
                version=version_proc,
                estado='PENDIENTE',
                total_paginas_esperadas=page_count,
                total_paginas_generadas=0,
                porcentaje_avance=0.00,
                prioridad=5,
                solicitado_por=user,
                es_actual=True
            )

            # Create ProcesamientoIntento record
            intento = ProcesamientoIntento.objects.using('periodico_db').create(
                procesamiento=procesamiento,
                pri_numero_intento=1,
                pri_estado='CREADO',
                pri_solicitado_por=user,
                edi_id=edition.id
            )

            # 10. Transition edition state to PENDIENTE_PROCESAMIENTO
            old_estado = edition.estado
            edition.estado = EstadoEdicion.PENDIENTE_PROCESAMIENTO
            edition.actualizado_por = user
            edition.fecha_actualizacion = timezone.now()
            edition.save(using='periodico_db')

            # Create histories and audits
            EdicionHistorial.objects.using('periodico_db').create(
                edicion=edition,
                tipo_evento=EventoEdicionHistorial.CARGA_PDF,
                estado_anterior=old_estado,
                estado_nuevo=EstadoEdicion.PENDIENTE_PROCESAMIENTO,
                valores_anteriores={"estado": old_estado},
                valores_nuevos={
                    "estado": EstadoEdicion.PENDIENTE_PROCESAMIENTO,
                    "archivo_id": archivo.id
                },
                realizado_por=user,
                direccion_ip=ip_address,
                resultado='EXITOSO'
            )

            AuditService.record_event(
                usuario=user,
                emp_id=company_id,
                modulo=AuditoriaModulo.M05,
                accion=AuditoriaAccion.EDICION_PDF_CARGADO,
                entidad="Edicion",
                entidad_id=str(edition.id),
                valores_nuevos={
                    "archivo_id": archivo.id,
                    "estado": EstadoEdicion.PENDIENTE_PROCESAMIENTO
                },
                resultado=AuditoriaResultado.EXITOSO,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # 11. Enqueue Celery task on commit
            from apps.processing.tasks import process_edition_pdf_task
            transaction.on_commit(
                lambda: process_edition_pdf_task.delay(intento.id),
                using='periodico_db'
            )

    except Exception as db_err:
        # Delete file if database operations fail
        if relative_path:
            StorageService.delete_private_file(relative_path)
        raise db_err

    return edition
