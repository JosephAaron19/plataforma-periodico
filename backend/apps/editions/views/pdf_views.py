from django.http import Http404
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from apps.authorization.permissions.drf_permissions import (
    IsAuthenticatedAndActive, HasCompanyPermission
)
from apps.editions.selectors.edition_selectors import get_company_edition_by_id
from apps.files.services.pdf_upload_service import upload_edition_pdf
from apps.files.serializers.file_serializers import ArchivoMetadataSerializer
from apps.processing.serializers.processing_serializers import ProcessingStatusSerializer
from apps.editions.serializers.edition_serializers import EditionDetailSerializer

from apps.processing.models.procesamiento import Procesamiento
from apps.processing.models.procesamiento_intento import ProcesamientoIntento
from apps.editions.models.edicion_archivo import EdicionArchivo
from apps.editions.models.edicion import Edicion
from apps.editions.constants import EstadoEdicion, EventoEdicionHistorial
from apps.editions.models.edicion_historial import EdicionHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaAccion, AuditoriaModulo, AuditoriaResultado

class CompanyEditionPDFView(generics.GenericAPIView):
    """
    POST: Uploads the main PDF file for an edition.
    Validates magic bytes, file signature (real MIME type), plans and storage limits,
    marks previous file as replaced, and enqueues the Celery processing task.

    GET: Retrieves metadata of the current active PDF of the edition, without exposing private storage paths.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission]
    required_permission = 'EDICION_EDITAR'
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, emp_id, edi_id):
        edition = get_company_edition_by_id(int(emp_id), int(edi_id))
        if not edition:
            raise Http404("La edición especificada no existe o fue eliminada.")
            
        pdf_association = EdicionArchivo.objects.using('periodico_db').filter(
            edicion=edition,
            tipo_archivo='PDF_ORIGINAL',
            es_actual=True
        ).select_related('archivo').first()
        
        if not pdf_association or not pdf_association.archivo:
            raise Http404("No se ha cargado un PDF para esta edición.")
            
        serializer = ArchivoMetadataSerializer(pdf_association.archivo)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, emp_id, edi_id):
        if 'file' not in request.FILES:
            raise ValidationError({"detail": "No se proporcionó ningún archivo en la solicitud."})
        
        uploaded_file = request.FILES['file']
        
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        try:
            # Call upload PDF service
            edition = upload_edition_pdf(
                company_id=int(emp_id),
                edition_id=int(edi_id),
                user=request.user,
                uploaded_file=uploaded_file,
                ip_address=ip_addr,
                user_agent=user_agent
            )
        except ValidationError as ve:
            # DRF validation error
            raise ve
        except Exception as e:
            # Wrap standard exceptions
            raise ValidationError({"detail": str(e)})
            
        output_serializer = EditionDetailSerializer(edition)
        return Response(
            {
                "detail": "PDF subido y proceso de procesamiento encolado correctamente.",
                "edition": output_serializer.data
            },
            status=status.HTTP_202_ACCEPTED
        )


class CompanyEditionProcessingStatusView(generics.GenericAPIView):
    """
    GET: Retrieves the status, progress and errors of the latest processing run for an edition.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission]
    required_permission = 'PROCESAMIENTO_VER'

    def get(self, request, emp_id, edi_id):
        edition = get_company_edition_by_id(int(emp_id), int(edi_id))
        if not edition:
            raise Http404("La edición especificada no existe o fue eliminada.")
            
        processing = Procesamiento.objects.using('periodico_db').filter(
            edicion=edition,
            es_actual=True
        ).first()
        
        if not processing:
            raise Http404("No existe un proceso de procesamiento para esta edición.")
            
        serializer = ProcessingStatusSerializer(processing)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyEditionProcessingRetryView(generics.GenericAPIView):
    """
    POST: Retries a failed processing run if the current processing is in ERROR state.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission]
    required_permission = 'PROCESAMIENTO_GESTIONAR'

    def post(self, request, emp_id, edi_id):
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        with transaction.atomic(using='periodico_db'):
            edition = Edicion.objects.using('periodico_db').select_for_update().get(
                id=int(edi_id),
                empresa_id=int(emp_id),
                eliminado=False
            )
            
            processing = Procesamiento.objects.using('periodico_db').select_for_update().filter(
                edicion=edition,
                es_actual=True
            ).first()
            
            if not processing:
                raise Http404("No existe un proceso de procesamiento para esta edición.")
                
            if processing.estado != 'ERROR':
                raise ValidationError("El procesamiento actual no se encuentra en estado de ERROR para poder reintentarse.")
                
            # Create a new ProcesamientoIntento record
            attempts_count = ProcesamientoIntento.objects.using('periodico_db').filter(procesamiento=processing).count()
            
            intento = ProcesamientoIntento.objects.using('periodico_db').create(
                procesamiento=processing,
                pri_numero_intento=attempts_count + 1,
                pri_estado='CREADO',
                pri_solicitado_por=request.user,
                edi_id=edition.id
            )
            
            # Reset processing status
            processing.estado = 'PENDIENTE'
            processing.porcentaje_avance = 0.00
            processing.total_paginas_generadas = 0
            processing.fecha_inicio = None
            processing.fecha_fin = None
            processing.resultado_resumen = "Reintento de procesamiento encolado."
            processing.save(using='periodico_db')
            
            # Reset edition status to PENDIENTE_PROCESAMIENTO
            old_edition_estado = edition.estado
            edition.estado = EstadoEdicion.PENDIENTE_PROCESAMIENTO
            edition.save(using='periodico_db')
            
            # Record histories and audits
            EdicionHistorial.objects.using('periodico_db').create(
                edicion=edition,
                tipo_evento=EventoEdicionHistorial.SOLICITUD_PROCESAMIENTO,
                estado_anterior=old_edition_estado,
                estado_nuevo=EstadoEdicion.PENDIENTE_PROCESAMIENTO,
                valores_anteriores={"estado": old_edition_estado},
                valores_nuevos={"estado": EstadoEdicion.PENDIENTE_PROCESAMIENTO},
                realizado_por=request.user,
                direccion_ip=ip_addr,
                resultado='EXITOSO'
            )
            
            AuditService.record_event(
                usuario=request.user,
                emp_id=int(emp_id),
                modulo=AuditoriaModulo.M05,
                accion=AuditoriaAccion.PROCESAMIENTO_REINTENTADO,
                entidad="Edicion",
                entidad_id=str(edition.id),
                valores_nuevos={
                    "estado": EstadoEdicion.PENDIENTE_PROCESAMIENTO,
                    "intento_numero": intento.pri_numero_intento
                },
                resultado=AuditoriaResultado.EXITOSO,
                ip_address=ip_addr,
                user_agent=user_agent
            )
            
            # Enqueue Celery task on commit
            from apps.processing.tasks import process_edition_pdf_task
            transaction.on_commit(
                lambda: process_edition_pdf_task.delay(intento.id),
                using='periodico_db'
            )
            
        return Response(
            {"detail": "Reintento de procesamiento encolado exitosamente."},
            status=status.HTTP_202_ACCEPTED
        )


class CompanyEditionProcessingCancelView(generics.GenericAPIView):
    """
    POST: Cancels a pending or running processing run.
    """
    permission_classes = [IsAuthenticatedAndActive, HasCompanyPermission]
    required_permission = 'PROCESAMIENTO_GESTIONAR'

    def post(self, request, emp_id, edi_id):
        ip_addr = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        with transaction.atomic(using='periodico_db'):
            edition = Edicion.objects.using('periodico_db').select_for_update().get(
                id=int(edi_id),
                empresa_id=int(emp_id),
                eliminado=False
            )
            
            processing = Procesamiento.objects.using('periodico_db').select_for_update().filter(
                edicion=edition,
                es_actual=True
            ).first()
            
            if not processing:
                raise Http404("No existe un proceso de procesamiento para esta edición.")
                
            if processing.estado not in ['PENDIENTE', 'PROCESANDO']:
                raise ValidationError("El procesamiento actual no está en ejecución para poder cancelarse.")
                
            # Update parent processing status
            processing.estado = 'CANCELADO'
            processing.fecha_cancelacion = timezone.now()
            processing.motivo_cancelacion = f"Cancelado administrativamente por {request.user.get_full_name()}."
            processing.resultado_resumen = "Procesamiento cancelado por el usuario."
            processing.save(using='periodico_db')
            
            # Update all active attempts
            ProcesamientoIntento.objects.using('periodico_db').filter(
                procesamiento=processing,
                pri_estado__in=['CREADO', 'EN_COLA', 'EJECUTANDO']
            ).update(
                pri_estado='CANCELADO',
                pri_resultado='CANCELADO',
                pri_fecha_fin=timezone.now()
            )
            
            # Transition edition state to ERROR (or back to BORRADOR, but ERROR fits transitions)
            old_edition_estado = edition.estado
            edition.estado = EstadoEdicion.ERROR
            edition.save(using='periodico_db')
            
            # Record histories and audits
            EdicionHistorial.objects.using('periodico_db').create(
                edicion=edition,
                tipo_evento=EventoEdicionHistorial.PROCESAMIENTO_ERROR, # No cancellation event in constants, using error
                estado_anterior=old_edition_estado,
                estado_nuevo=EstadoEdicion.ERROR,
                valores_anteriores={"estado": old_edition_estado},
                valores_nuevos={"estado": EstadoEdicion.ERROR},
                realizado_por=request.user,
                direccion_ip=ip_addr,
                resultado='EXITOSO'
            )
            
            AuditService.record_event(
                usuario=request.user,
                emp_id=int(emp_id),
                modulo=AuditoriaModulo.M05,
                accion=AuditoriaAccion.PROCESAMIENTO_CANCELADO,
                entidad="Edicion",
                entidad_id=str(edition.id),
                valores_nuevos={
                    "estado": EstadoEdicion.ERROR
                },
                resultado=AuditoriaResultado.EXITOSO,
                ip_address=ip_addr,
                user_agent=user_agent
            )
            
        return Response(
            {"detail": "Procesamiento cancelado exitosamente."},
            status=status.HTTP_200_OK
        )
