from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_historial import EdicionHistorial
from apps.editions.constants import EstadoEdicion, EventoEdicionHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaAccion, AuditoriaModulo, AuditoriaResultado

def reactivate_edition(*, company_id: int, edition_id: int, user: Usuario, target_state: str, ip_address: str = None, user_agent: str = None) -> Edicion:
    """
    Reactivates a suspended edition.
    Supports transitioning to PUBLICADA (direct reactivate) or BORRADOR (return to draft).
    If target_state is BORRADOR, cleans the publication date to satisfy the ck_edi_publicacion constraint.
    """
    if target_state not in [EstadoEdicion.PUBLICADA, EstadoEdicion.BORRADOR]:
        raise ValidationError("El estado destino para reactivación debe ser PUBLICADA o BORRADOR.")

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

        # 2. Check transition compatibility
        if edition.estado != EstadoEdicion.SUSPENDIDA:
            raise ValidationError(f"Solo se pueden reactivar ediciones SUSPENDIDAS. Estado actual: '{edition.estado}'.")

        # 3. Validations for target_state = PUBLICADA
        if target_state == EstadoEdicion.PUBLICADA:
            from apps.companies.models.empresa import Empresa
            from apps.plans.selectors.plan_selectors import get_company_active_plan
            from apps.processing.models.procesamiento import Procesamiento

            try:
                company = Empresa.objects.using('periodico_db').get(id=company_id, eliminado=False)
            except Empresa.DoesNotExist:
                raise ValidationError("La empresa especificada no existe o fue eliminada.")

            is_company_active = (company.estado == 'ACTIVA')
            is_plan_active = (get_company_active_plan(company.id) is not None)
            has_prev_pub = (edition.fecha_publicacion is not None)
            has_completed_processing = Procesamiento.objects.using('periodico_db').filter(
                edicion=edition,
                estado='COMPLETADO',
                es_actual=True
            ).exists()

            if not (is_company_active and is_plan_active and has_prev_pub and has_completed_processing):
                target_state = EstadoEdicion.BORRADOR

        # 4. Transition state
        old_estado = edition.estado
        edition.estado = target_state
        
        # Clean physical publication date if returning to BORRADOR
        if target_state == EstadoEdicion.BORRADOR:
            edition.fecha_publicacion = None
            
        edition.actualizado_por = user
        edition.fecha_actualizacion = now
        edition.save(using='periodico_db')

        # 4. Create history record
        EdicionHistorial.objects.using('periodico_db').create(
            edicion=edition,
            tipo_evento=EventoEdicionHistorial.REACTIVACION,
            estado_anterior=old_estado,
            estado_nuevo=target_state,
            valores_anteriores={"estado": old_estado},
            valores_nuevos={"estado": target_state},
            realizado_por=user,
            direccion_ip=ip_address,
            resultado='EXITOSO'
        )

        # 5. Record audit event
        AuditService.record_event(
            usuario=user,
            emp_id=company_id,
            modulo=AuditoriaModulo.M05,
            accion=AuditoriaAccion.EDICION_REACTIVADA,
            entidad="Edicion",
            entidad_id=str(edition.id),
            valores_nuevos={
                "id": edition.id,
                "estado": target_state
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return edition
