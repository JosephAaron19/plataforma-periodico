from apps.plans.selectors.plan_selectors import get_company_active_plan
from apps.plans.models.plan_funcionalidad import PlanFuncionalidad
from apps.companies.models.empresa import Empresa
from django.db.models import Q

def has_plan_feature(company, permission_code: str) -> bool:
    """
    Checks if the active plan of the company enables the feature corresponding to the permission_code.
    Rules:
    - Company must exist, have state 'ACTIVA', and not be soft-deleted.
    - Must have a currently active EmpresaPlan.
    - Active plan must have a PlanFuncionalidad record where plf_habilitada = True and
      (plf_codigo_funcionalidad = permission_code OR active per_permiso.per_codigo = permission_code).
    """
    if not company:
        return False
        
    if isinstance(company, int):
        try:
            company_obj = Empresa.objects.using('periodico_db').get(id=company, eliminado=False)
        except Empresa.DoesNotExist:
            return False
    else:
        company_obj = company

    if company_obj.estado != 'ACTIVA' or company_obj.eliminado:
        return False

    active_plan_relation = get_company_active_plan(company_obj.id)
    if not active_plan_relation:
        return False

    return PlanFuncionalidad.objects.using('periodico_db').filter(
        plan_id=active_plan_relation.plan_id,
        habilitada=True
    ).filter(
        Q(codigo_funcionalidad=permission_code) |
        Q(permiso__codigo=permission_code, permiso__estado='ACTIVO')
    ).exists()
