import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.companies.models.empresa import Empresa
from apps.plans.models.empresa_plan import EmpresaPlan
from apps.plans.selectors.plan_selectors import get_plan_by_code
from apps.plans.services.plan_limit_service import get_company_usage
from apps.companies.models.empresa_historial import EmpresaHistorial
from apps.audit.services.audit_service import AuditService
from apps.audit.constants import AuditoriaModulo, AuditoriaAccion, AuditoriaResultado

logger = logging.getLogger(__name__)

def change_company_plan(
    *,
    empresa_id: int,
    plan_code: str,
    reason: str,
    solicitante,
    ip_address: str = None
) -> EmpresaPlan:
    """
    Administratively switches a company's plan.
    Locks the current active plan assignment before switching to prevent race conditions.
    """
    # 1. Validate company exists and is active
    try:
        empresa = Empresa.objects.using('periodico_db').get(id=empresa_id, eliminado=False)
    except Empresa.DoesNotExist:
        raise ValidationError("La empresa especificada no existe.")

    if empresa.estado != 'ACTIVA':
        raise ValidationError("No se puede cambiar el plan de una empresa que no está activa.")

    # 2. Validate new plan exists and is active
    new_plan = get_plan_by_code(plan_code)

    # 3. Process the change in a transaction with write lock
    with transaction.atomic(using='periodico_db'):
        active_relations = list(EmpresaPlan.objects.using('periodico_db').select_for_update().filter(
            empresa_id=empresa_id,
            estado='ACTIVO'
        ))

        if len(active_relations) > 1:
            raise ValidationError("Inconsistencia detectada: la empresa tiene múltiples planes activos simultáneamente.")

        old_relation = active_relations[0] if active_relations else None
        old_plan = None
        now = timezone.now()

        if old_relation:
            old_plan = old_relation.plan
            old_relation.estado = 'REEMPLAZADO'
            old_relation.fecha_fin = now
            old_relation.motivo_cambio = reason
            old_relation.fecha_actualizacion = now
            old_relation.save(using='periodico_db')

        # Create new plan assignment
        new_relation = EmpresaPlan(
            empresa=empresa,
            plan=new_plan,
            fecha_inicio=now,
            precio_contratado=new_plan.precio,
            moneda=new_plan.moneda,
            periodicidad=new_plan.periodicidad,
            estado='ACTIVO',
            asignado_por=solicitante,
            renovacion_automatica=False,
            fecha_creacion=now
        )
        new_relation.save(using='periodico_db')

        # 4. Check for overconsumption under the new plan
        usage = get_company_usage(empresa_id)
        overconsumption = False
        over_details = []

        if new_plan.limite_usuarios is not None and usage["users"] > new_plan.limite_usuarios:
            overconsumption = True
            over_details.append(f"usuarios ({usage['users']} > {new_plan.limite_usuarios})")

        if new_plan.limite_ediciones_mes is not None and usage["editions"] > new_plan.limite_ediciones_mes:
            overconsumption = True
            over_details.append(f"ediciones ({usage['editions']} > {new_plan.limite_ediciones_mes})")

        new_plan_storage_bytes = (new_plan.limite_storage_mb * 1024 * 1024) if new_plan.limite_storage_mb is not None else None
        if new_plan_storage_bytes is not None and usage["storage_bytes"] > new_plan_storage_bytes:
            overconsumption = True
            over_details.append(f"almacenamiento ({usage['storage_bytes']} > {new_plan_storage_bytes} bytes)")

        action_code = AuditoriaAccion.PLAN_EMPRESA_CAMBIADO
        if overconsumption:
            action_code = AuditoriaAccion.CAMBIO_PLAN_CON_SOBRECONSUMO
            logger.warning(
                f"Cambio de plan realizado con sobreconsumo para empresa {empresa_id} ({empresa.nombre_comercial}). "
                f"Detalle: {', '.join(over_details)}"
            )

        # 5. Save to EmpresaHistorial
        historial = EmpresaHistorial(
            empresa=empresa,
            tipo_evento='CAMBIO_PLAN',
            estado_anterior=empresa.estado,
            estado_nuevo=empresa.estado,
            motivo=reason,
            detalle_anterior={
                "plan_id": old_plan.id,
                "plan_codigo": old_plan.codigo
            } if old_plan else None,
            detalle_nuevo={
                "plan_id": new_plan.id,
                "plan_codigo": new_plan.codigo
            },
            realizado_por=solicitante,
            direccion_ip=ip_address,
            resultado='EXITOSO'
        )
        historial.save(using='periodico_db')

        # 6. Save audit log record
        AuditService.record_event(
            usuario=solicitante,
            emp_id=empresa_id,
            modulo=AuditoriaModulo.M03,
            accion=action_code,
            entidad='EmpresaPlan',
            entidad_id=str(new_relation.id),
            valores_anteriores={
                "plan_id": old_plan.id,
                "plan_codigo": old_plan.codigo
            } if old_plan else {},
            valores_nuevos={
                "plan_id": new_plan.id,
                "plan_codigo": new_plan.codigo
            },
            resultado=AuditoriaResultado.EXITOSO,
            motivo=reason,
            ip_address=ip_address,
            throw_on_error=False
        )

    return new_relation
