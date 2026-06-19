from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.companies.models.empresa import Empresa
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_historial import EdicionHistorial
from apps.editions.models.edicion_programacion import EdicionProgramacion
from apps.editions.constants import EstadoEdicion, EventoEdicionHistorial
from apps.plans.services.plan_feature_service import has_plan_feature
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaAccion, AuditoriaModulo, AuditoriaResultado

def publish_edition(*, company_id: int, edition_id: int, user: Usuario = None, proceso_origen: str = None, ip_address: str = None, user_agent: str = None) -> Edicion:
    """
    Publishes an edition.
    Can be run immediately by a user, or scheduled/asynchronously by a Celery process.
    """
    if not user and not proceso_origen:
        raise ValidationError("Se requiere un usuario o un proceso de origen para publicar la edición.")

    now = timezone.now()

    with transaction.atomic(using='periodico_db'):
        # 1. Lock the edition record
        try:
            edition = Edicion.objects.using('periodico_db').select_for_update().get(
                id=edition_id,
                empresa_id=company_id,
                eliminado=False
            )
        except Edicion.DoesNotExist:
            raise ValidationError("La edición especificada no existe o fue eliminada.")

        # 2. Check current state transition compatibility
        if edition.estado not in [EstadoEdicion.BORRADOR, EstadoEdicion.PROGRAMADA]:
            raise ValidationError(f"No se puede publicar una edición en estado '{edition.estado}'.")

        # 3. Validate company and plan
        try:
            company = Empresa.objects.using('periodico_db').get(id=company_id, eliminado=False)
        except Empresa.DoesNotExist:
            raise ValidationError("La empresa especificada no existe o fue eliminada.")

        if not has_plan_feature(company, "EDICION_PUBLICAR"):
            raise ValidationError("El plan de la empresa no habilita la publicación de ediciones.")

        # 4. Cancel/Mark schedules as executed or cancelled
        pending_scheds = EdicionProgramacion.objects.using('periodico_db').filter(
            edicion=edition,
            estado='PENDIENTE'
        )
        for sched in pending_scheds:
            if proceso_origen == 'CELERY_TASK':
                sched.estado = 'EJECUTADA'
                sched.fecha_ejecucion = now
                sched.resultado = 'EXITOSO'
            else:
                sched.estado = 'CANCELADA'
                sched.fecha_cancelacion = now
                sched.cancelado_por = user
                sched.motivo_cancelacion = "Publicación inmediata ejecutada por el usuario."
                sched.resultado = 'RECHAZADO'
            sched.save(using='periodico_db')

        # 5. Transition state
        old_estado = edition.estado
        edition.estado = EstadoEdicion.PUBLICADA
        edition.fecha_publicacion = now
        
        if user:
            edition.actualizado_por = user
            
        edition.fecha_actualizacion = now
        edition.save(using='periodico_db')

        # 6. Create history record
        EdicionHistorial.objects.using('periodico_db').create(
            edicion=edition,
            tipo_evento=EventoEdicionHistorial.PUBLICACION,
            estado_anterior=old_estado,
            estado_nuevo=EstadoEdicion.PUBLICADA,
            valores_anteriores={"estado": old_estado},
            valores_nuevos={
                "estado": EstadoEdicion.PUBLICADA,
                "fecha_publicacion": now.isoformat()
            },
            realizado_por=user,
            proceso_origen=proceso_origen,
            direccion_ip=ip_address,
            resultado='EXITOSO'
        )

        # 7. Record audit event
        AuditService.record_event(
            usuario=user,
            emp_id=company_id,
            modulo=AuditoriaModulo.M05,
            accion=AuditoriaAccion.EDICION_PUBLICADA,
            entidad="Edicion",
            entidad_id=str(edition.id),
            valores_nuevos={
                "id": edition.id,
                "estado": EstadoEdicion.PUBLICADA,
                "fecha_publicacion": now.isoformat()
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent,
            proceso_origen=proceso_origen
        )

        return edition
