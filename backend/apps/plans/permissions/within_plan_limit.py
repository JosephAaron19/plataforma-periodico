from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, APIException
from apps.plans.services.plan_limit_service import check_user_limit, check_edition_limit, check_storage_limit
from apps.companies.models.empresa import Empresa

class PlanLimitExceeded(APIException):
    status_code = 409
    default_detail = 'Límite del plan comercial alcanzado.'
    default_code = 'plan_limit_exceeded'

class WithinPlanLimit(BasePermission):
    """
    DRF permission class to check if the company is within plan limits.
    Reads required_plan_limit from the view class (options: 'users', 'editions', 'storage').
    """
    def has_permission(self, request, view):
        required_limit = getattr(view, 'required_plan_limit', None)
        if not required_limit:
            return True

        emp_id = view.kwargs.get('emp_id')
        if not emp_id:
            emp_id = request.query_params.get('emp_id') or request.data.get('emp_id')

        if not emp_id:
            raise PermissionDenied("Contexto de empresa (emp_id) no proporcionado.")

        try:
            company = Empresa.objects.using('periodico_db').get(id=emp_id, eliminado=False)
        except Empresa.DoesNotExist:
            raise PermissionDenied("La empresa especificada no existe o fue eliminada.")

        if required_limit == 'users':
            res = check_user_limit(company)
        elif required_limit == 'editions':
            res = check_edition_limit(company)
        elif required_limit == 'storage':
            additional_bytes = int(request.data.get('file_size', 0) or request.query_params.get('file_size', 0))
            res = check_storage_limit(company, additional_bytes=additional_bytes)
        else:
            return True

        if not res["allowed"]:
            raise PlanLimitExceeded({
                "allowed": False,
                "code": res.get("code", "PLAN_LIMIT_REACHED"),
                "message": res["message"],
                "limit": res.get("limit") or res.get("limit_bytes"),
                "used": res.get("used") or res.get("used_bytes")
            })

        return True
