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

def schedule_publication(*, company_id: int, edition_id: int, user: Usuario, scheduled_at, timezone_name: str = 'America/Lima', ip_address: str = None, user_agent: str = None) -> Edicion:
    """
    Schedules an edition for publication at a future date.
    Validates current state, future datetime, and plan features.
    If already scheduled, cancels the previous scheduling correctly.
    """
    now = timezone.now()
    if scheduled_at <= now:
        raise ValidationError("La fecha programada debe ser en el futuro.")

    with transaction.atomic(using='periodico_db'):
        # 1. Lock the edition
        try:
            edition = Edicion.objects.using('periodico_db').select_for_update().get(
                id=edition_id,
                empresa_id=company_id,
                eliminado=False
            )
        except Edicion.DoesNotExist:
            raise ValidationError("La edición especificada no existe o fue eliminada.")

        # 2. Validate company and plan
        try:
            company = Empresa.objects.using('periodico_db').get(id=company_id, eliminado=False)
        except Empresa.DoesNotExist:
            raise ValidationError("La empresa especificada no existe o fue eliminada.")

        if not has_plan_feature(company, "EDICION_PUBLICAR"):
            raise ValidationError("El plan de la empresa no habilita la programación o publicación de ediciones.")

        # 3. Check transition compatibility
        if edition.estado not in [EstadoEdicion.BORRADOR, EstadoEdicion.PROGRAMADA]:
            raise ValidationError(f"No se puede programar una edición en estado '{edition.estado}'.")

        # 4. Cancel previous pending schedules
        pending_scheds = EdicionProgramacion.objects.using('periodico_db').filter(
            edicion=edition,
            estado='PENDIENTE'
        )
        for sched in pending_scheds:
            sched.estado = 'CANCELADA'
            sched.fecha_cancelacion = now
            sched.cancelado_por = user
            sched.motivo_cancelacion = "Reemplazada por nueva programación."
            sched.resultado = 'RECHAZADO'
            sched.save(using='periodico_db')

        # 5. Create new schedule record
        EdicionProgramacion.objects.using('periodico_db').create(
            edicion=edition,
            fecha_programada=scheduled_at,
            zona_horaria=timezone_name,
            estado='PENDIENTE',
            programado_por=user,
            fecha_creacion=now
        )

        # 6. Update edition state to PROGRAMADA
        old_estado = edition.estado
        edition.estado = EstadoEdicion.PROGRAMADA
        edition.actualizado_por = user
        edition.fecha_actualizacion = now
        edition.save(using='periodico_db')

        # 7. Create history record
        EdicionHistorial.objects.using('periodico_db').create(
            edicion=edition,
            tipo_evento=EventoEdicionHistorial.PROGRAMACION,
            estado_anterior=old_estado,
            estado_nuevo=EstadoEdicion.PROGRAMADA,
            valores_anteriores={"estado": old_estado},
            valores_nuevos={
                "estado": EstadoEdicion.PROGRAMADA,
                "fecha_programada": scheduled_at.isoformat()
            },
            realizado_por=user,
            direccion_ip=ip_address,
            resultado='EXITOSO'
        )

        # 8. Record audit event
        AuditService.record_event(
            usuario=user,
            emp_id=company_id,
            modulo=AuditoriaModulo.M05,
            accion=AuditoriaAccion.EDICION_PROGRAMADA,
            entidad="Edicion",
            entidad_id=str(edition.id),
            valores_nuevos={
                "id": edition.id,
                "estado": EstadoEdicion.PROGRAMADA,
                "fecha_programada": scheduled_at.isoformat()
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return edition
