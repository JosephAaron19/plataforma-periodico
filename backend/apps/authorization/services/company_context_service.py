from rest_framework.exceptions import PermissionDenied
from apps.authorization.selectors.auth_selector import get_user_company_relation

def resolve_user_company_context(user, emp_id) -> None:
    """
    Validates if the authenticated user has an active relation with the given company.
    If the relationship is active, returns the Empresa instance; otherwise raises PermissionDenied.
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("Debe estar autenticado para acceder al contexto empresarial.")

    if not emp_id:
        raise PermissionDenied("Identificador de empresa no proporcionado.")

    relation = get_user_company_relation(user.id, emp_id)
    if not relation:
        raise PermissionDenied("No tiene autorización para acceder a esta empresa o la empresa está inactiva.")

    return relation.empresa
