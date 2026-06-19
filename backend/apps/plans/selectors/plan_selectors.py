from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from apps.plans.models.plan import Plan
from apps.plans.models.empresa_plan import EmpresaPlan

def get_active_plans():
    """
    Returns active and public plans ordered by their commercial order.
    """
    return Plan.objects.using('periodico_db').filter(
        estado='ACTIVO',
        es_publico=True
    ).order_by('orden')

def get_plan_by_code(code: str) -> Plan:
    """
    Returns an active plan by its unique code.
    """
    try:
        return Plan.objects.using('periodico_db').get(
            codigo=code,
            estado='ACTIVO'
        )
    except Plan.DoesNotExist:
        raise ValidationError(f"El plan con código '{code}' no existe o no está activo.")

def get_company_active_plan(company_id: int) -> EmpresaPlan:
    """
    Resolves the currently active and vigent plan of a company.
    Rules:
    - Must be in 'ACTIVO' state.
    - Current timezone must be between epl_fecha_inicio and epl_fecha_fin (inclusive/exclusive),
      or epl_fecha_fin must be null.
    - If multiple active plans exist concurrent due to database inconsistency,
      raises a ValidationError to prevent choosing arbitrarily.
    """
    now = timezone.now()
    active_plans = list(EmpresaPlan.objects.using('periodico_db').select_related('plan').filter(
        empresa_id=company_id,
        estado='ACTIVO',
        fecha_inicio__lte=now
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=now)
    ))

    if len(active_plans) > 1:
        raise ValidationError("Inconsistencia detectada: la empresa tiene múltiples planes activos simultáneamente.")
    elif len(active_plans) == 1:
        return active_plans[0]
    return None
