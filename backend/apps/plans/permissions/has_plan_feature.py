from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from apps.plans.services.plan_feature_service import has_plan_feature
from apps.companies.models.empresa import Empresa

class HasPlanFeature(BasePermission):
    """
    DRF permission class to check if the company's active plan enables the required feature.
    Reads required_plan_feature from the view class.
    """
    def has_permission(self, request, view):
        required_feature = getattr(view, 'required_plan_feature', None)
        if not required_feature:
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

        if not has_plan_feature(company, required_feature):
            raise PermissionDenied(f"El plan de la empresa no habilita la funcionalidad requerida: '{required_feature}'.")

        return True
