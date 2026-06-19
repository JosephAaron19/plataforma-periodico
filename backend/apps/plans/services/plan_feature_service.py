from apps.plans.selectors.plan_selectors import get_company_active_plan
from apps.plans.models.plan_funcionalidad import PlanFuncionalidad
from django.db.models import Q

def has_plan_feature(company, permission_code: str) -> bool:
    """
    Checks if the active plan of the company enables the feature corresponding to the permission_code.
    Rules:
    - Must have a currently active EmpresaPlan.
    - Active plan must have a PlanFuncionalidad record where plf_habilitada = True and
      (plf_codigo_funcionalidad = permission_code OR per_permiso.per_codigo = permission_code).
    """
    if not company:
        return False
        
    company_id = company if isinstance(company, int) else company.id
    active_plan_relation = get_company_active_plan(company_id)
    if not active_plan_relation:
        return False

    return PlanFuncionalidad.objects.using('periodico_db').filter(
        plan_id=active_plan_relation.plan_id,
        habilitada=True
    ).filter(
        Q(codigo_funcionalidad=permission_code) | Q(permiso__codigo=permission_code)
    ).exists()
