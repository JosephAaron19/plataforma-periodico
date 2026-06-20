from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models.usuario import Usuario
from apps.editions.models.edicion import Edicion
from apps.editions.models.edicion_historial import EdicionHistorial
from apps.editions.constants import EstadoEdicion, EventoEdicionHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaAccion, AuditoriaModulo, AuditoriaResultado

def suspend_edition(*, company_id: int, edition_id: int, user: Usuario, reason: str = None, ip_address: str = None, user_agent: str = None) -> Edicion:
    """
    Suspends a published edition.
    Changes the physical state to SUSPENDIDA and registers it in history and audit.
    """
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
        if edition.estado != EstadoEdicion.PUBLICADA:
            raise ValidationError(f"Solo se pueden suspender ediciones PUBLICADAS. Estado actual: '{edition.estado}'.")

        # 3. Transition state
        old_estado = edition.estado
        edition.estado = EstadoEdicion.SUSPENDIDA
        edition.actualizado_por = user
        edition.fecha_actualizacion = now
        edition.save(using='periodico_db')

        # 4. Create history record
        EdicionHistorial.objects.using('periodico_db').create(
            edicion=edition,
            tipo_evento=EventoEdicionHistorial.SUSPENSION,
            estado_anterior=old_estado,
            estado_nuevo=EstadoEdicion.SUSPENDIDA,
            valores_anteriores={"estado": old_estado},
            valores_nuevos={"estado": EstadoEdicion.SUSPENDIDA},
            motivo=reason or "Suspensión administrativa",
            realizado_por=user,
            direccion_ip=ip_address,
            resultado='EXITOSO'
        )

        # 5. Record audit event
        AuditService.record_event(
            usuario=user,
            emp_id=company_id,
            modulo=AuditoriaModulo.M05,
            accion=AuditoriaAccion.EDICION_SUSPENDIDA,
            entidad="Edicion",
            entidad_id=str(edition.id),
            valores_nuevos={
                "id": edition.id,
                "estado": EstadoEdicion.SUSPENDIDA,
                "motivo": reason
            },
            resultado=AuditoriaResultado.EXITOSO,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return edition
