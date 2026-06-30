import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from apps.editions.models.edicion_programacion import EdicionProgramacion
from apps.editions.models.edicion import Edicion
from apps.editions.constants import EstadoEdicion
from apps.editions.services.edition_publish_service import publish_edition

logger = logging.getLogger(__name__)

@shared_task(name="apps.editions.tasks.publish_scheduled_editions_task")
def publish_scheduled_editions_task():
    """
    Idempotent background task to execute publication of editions that have reached their scheduled time.
    Uses select_for_update to guarantee only one worker executes each programacion and prevents double publishing.
    """
    now = timezone.now()
    
    # Get all pending schedulings that are due
    pending_scheds = EdicionProgramacion.objects.using('periodico_db').filter(
        estado='PENDIENTE',
        fecha_programada__lte=now
    ).select_related('edicion')

    processed_count = 0
    
    for sched in pending_scheds:
        try:
            with transaction.atomic(using='periodico_db'):
                # 1. Lock scheduling record and re-verify state
                locked_sched = EdicionProgramacion.objects.using('periodico_db').select_for_update().get(id=sched.id)
                if locked_sched.estado != 'PENDIENTE':
                    logger.warning(f"Scheduling {sched.id} already processed or canceled. Skipping.")
                    continue

                # 2. Lock edition and verify it is still in PROGRAMADA state
                locked_edition = Edicion.objects.using('periodico_db').select_for_update().get(id=locked_sched.edicion.id)
                if locked_edition.estado != EstadoEdicion.PROGRAMADA:
                    # Update scheduling record to error/rejected because the edition state changed
                    locked_sched.estado = 'VENCIDA'
                    locked_sched.resultado = 'RECHAZADO'
                    locked_sched.detalle_error = f"La edición no está en estado PROGRAMADA. Estado actual: '{locked_edition.estado}'."
                    locked_sched.save(using='periodico_db')
                    continue

                # 2.b Revalidate company, active plan, plan feature and completed processing
                company = locked_edition.empresa
                if company.estado != 'ACTIVA' or company.eliminado:
                    locked_sched.estado = 'VENCIDA'
                    locked_sched.resultado = 'RECHAZADO'
                    locked_sched.detalle_error = f"La empresa '{company.razon_social}' no está activa o fue eliminada."
                    locked_sched.save(using='periodico_db')
                    continue

                from apps.plans.selectors.plan_selectors import get_company_active_plan
                from apps.plans.services.plan_feature_service import has_plan_feature
                if not get_company_active_plan(company.id):
                    locked_sched.estado = 'VENCIDA'
                    locked_sched.resultado = 'RECHAZADO'
                    locked_sched.detalle_error = "La empresa no tiene un plan activo asignado."
                    locked_sched.save(using='periodico_db')
                    continue

                if not has_plan_feature(company, "EDICION_PUBLICAR"):
                    locked_sched.estado = 'VENCIDA'
                    locked_sched.resultado = 'RECHAZADO'
                    locked_sched.detalle_error = "El plan de la empresa no habilita la publicación de ediciones."
                    locked_sched.save(using='periodico_db')
                    continue

                from apps.processing.models.procesamiento import Procesamiento
                has_completed_processing = Procesamiento.objects.using('periodico_db').filter(
                    edicion=locked_edition,
                    estado='COMPLETADO',
                    es_actual=True
                ).exists()

                if not has_completed_processing:
                    locked_sched.estado = 'VENCIDA'
                    locked_sched.resultado = 'RECHAZADO'
                    locked_sched.detalle_error = "La edición debe completar el procesamiento antes de publicarse."
                    locked_sched.save(using='periodico_db')
                    continue

                # 3. Publish the edition via the service
                publish_edition(
                    company_id=locked_edition.empresa_id,
                    edition_id=locked_edition.id,
                    proceso_origen='CELERY_TASK'
                )

                processed_count += 1

        except Exception as e:
            logger.error(f"Error publishing scheduled edition programacion {sched.id}: {str(e)}", exc_info=True)
            # Try to log the failure in the scheduling record in an isolated transaction
            try:
                with transaction.atomic(using='periodico_db'):
                    failed_sched = EdicionProgramacion.objects.using('periodico_db').select_for_update().get(id=sched.id)
                    if failed_sched.estado == 'PENDIENTE':
                        failed_sched.estado = 'ERROR'
                        failed_sched.resultado = 'ERROR'
                        failed_sched.detalle_error = str(e)
                        failed_sched.save(using='periodico_db')
            except Exception as inner_e:
                logger.error(f"Could not save scheduling error state for {sched.id}: {str(inner_e)}")

    return f"Processed {processed_count} scheduled editions successfully."


from datetime import timedelta

@shared_task(name="apps.editions.tasks.distribute_edition_to_subscribers_task")
def distribute_edition_to_subscribers_task(edition_id: int):
    """
    Distributes a newly published edition to all active subscribers of the company.
    For each active subscriber, creates an AccesoEdicion and registers a Notificacion.
    """
    from django.db import transaction
    from django.utils import timezone
    from apps.editions.models.edicion import Edicion
    from apps.purchases.models.compra import Compra
    from apps.access.models.acceso_edicion import AccesoEdicion
    from apps.access.models.acceso_tipo import AccesoTipo
    from apps.notifications.models.notificacion import Notificacion
    from django.db.models import Q

    logger.info(f"distribute_edition_to_subscribers_task: Iniciando distribución para edición {edition_id}")
    now = timezone.now()

    try:
        edition = Edicion.objects.using('periodico_db').get(id=edition_id, eliminado=False)
    except Edicion.DoesNotExist:
        logger.error(f"distribute_edition_to_subscribers_task: Edición {edition_id} no encontrada.")
        return "Edición no encontrada."

    company_id = edition.empresa_id

    # 1. Fetch all active subscriber purchases for this company
    plan_purchases = Compra.objects.using('periodico_db').filter(
        empresa_id=company_id,
        estado='PAGADA'
    ).filter(
        Q(referencia_interna__icontains='MENSUAL') |
        Q(referencia_interna__icontains='ANUAL') |
        Q(referencia_interna__icontains='DIARIO')
    ).select_related('usuario')

    # Get active type COMPRA
    try:
        tipo_acceso = AccesoTipo.objects.using('periodico_db').get(codigo='COMPRA', estado='ACTIVO')
    except AccesoTipo.DoesNotExist:
        logger.error("distribute_edition_to_subscribers_task: AccesoTipo 'COMPRA' no encontrado.")
        return "AccesoTipo 'COMPRA' no encontrado."

    # Validate PDF exists
    pdf_rel = edition.archivos_asociados.filter(
        tipo_archivo='PDF_ORIGINAL',
        es_actual=True,
        estado='ACTIVO',
        archivo__estado='DISPONIBLE',
        archivo__eliminado=False
    ).select_related('archivo').first()

    if not pdf_rel or not pdf_rel.archivo:
        logger.error(f"distribute_edition_to_subscribers_task: El PDF original para la edición {edition_id} no está disponible.")
        return "PDF no disponible."

    success_count = 0
    fail_count = 0

    for purchase in plan_purchases:
        user = purchase.usuario
        
        # Guard: Check user is active and not deleted
        if not user.is_active or getattr(user, 'eliminado', False):
            continue

        # Calculate subscription expiration
        ref_upper = purchase.referencia_interna.upper()
        duration_days = 0
        if "DIARIO" in ref_upper:
            duration_days = 1
        elif "MENSUAL" in ref_upper:
            duration_days = 30
        elif "ANUAL" in ref_upper:
            duration_days = 365

        start_date = purchase.fecha_confirmacion or purchase.fecha_creacion
        expiration_date = start_date + timedelta(days=duration_days)

        if now >= expiration_date:
            continue

        try:
            # Grant access atomically
            with transaction.atomic(using='periodico_db'):
                # Check if access already exists for this edition
                acceso_existente = AccesoEdicion.objects.using('periodico_db').filter(
                    usuario=user,
                    edicion=edition,
                    estado='ACTIVO'
                ).first()

                if not acceso_existente:
                    AccesoEdicion.objects.using('periodico_db').create(
                        usuario=user,
                        edicion=edition,
                        compra_id=None,
                        tipo_acceso=tipo_acceso,
                        fecha_inicio=now,
                        fecha_fin=expiration_date,
                        estado='ACTIVO',
                        origen_referencia='SUSCRIPCION_PLAN',
                        motivo=f"Acceso automático por plan de suscripción activo (compra_id={purchase.id})."
                    )
                
                # Create or update notification
                notif_existente = Notificacion.objects.using('periodico_db').filter(
                    usuario=user,
                    empresa_id=company_id,
                    entidad='Edicion',
                    entidad_id=str(edition.id)
                ).first()

                if not notif_existente:
                    notif = Notificacion.objects.using('periodico_db').create(
                        usuario=user,
                        empresa_id=company_id,
                        tipo='PUBLICACION',
                        titulo=f"Nueva edición publicada: {edition.titulo}",
                        mensaje=f"La edición '{edition.titulo}' ya está disponible en tu biblioteca.",
                        entidad='Edicion',
                        entidad_id=str(edition.id),
                        estado='ENVIADA',
                        fecha_envio=None
                    )
                    notif.fecha_envio = notif.fecha_creacion
                    notif.save(using='periodico_db')
                elif notif_existente.estado == 'ERROR':
                    notif_existente.estado = 'ENVIADA'
                    notif_existente.fecha_envio = notif_existente.fecha_creacion
                    notif_existente.save(using='periodico_db')

            success_count += 1
            logger.info(f"Edición {edition_id} distribuida con éxito al usuario {user.id}")

        except Exception as e:
            fail_count += 1
            logger.error(f"Error al distribuir edición {edition_id} al usuario {user.id}: {e}")
            try:
                # Log failure as a Notificacion
                with transaction.atomic(using='periodico_db'):
                    Notificacion.objects.using('periodico_db').create(
                        usuario=user,
                        empresa_id=company_id,
                        tipo='PUBLICACION',
                        titulo=f"Fallo de entrega: {edition.titulo}",
                        mensaje=str(e)[:500],
                        entidad='Edicion',
                        entidad_id=str(edition.id),
                        estado='ERROR',
                        fecha_envio=None
                    )
            except Exception as inner_e:
                logger.error(f"No se pudo registrar notificación fallida para usuario {user.id}: {inner_e}")

    return f"Distribución de Edición {edition_id} completada. Exitosos: {success_count}, Fallidos: {fail_count}"

