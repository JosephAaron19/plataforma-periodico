from rest_framework.exceptions import PermissionDenied
from apps.authorization.services.company_context_service import resolve_user_company_context

class CompanyContextMixin:
    """
    Mixin for Django REST Framework views to retrieve and validate the active company context.
    Ensures that the company ID is resolved from route parameter or X-Company-ID header
    and validated against active user-company relations.
    """
    def get_company_id(self) -> str:
        # 1. Resolve from URL parameters
        emp_id = self.kwargs.get('emp_id')
        
        # 2. Resolve from X-Company-ID header
        if not emp_id:
            emp_id = self.request.headers.get('X-Company-ID')
            
        return emp_id

    def get_company(self):
        """
        Retrieves the validated Empresa instance for the current request.
        """
        emp_id = self.get_company_id()
        if not emp_id:
            raise PermissionDenied("Identificador de empresa no proporcionado en la solicitud.")
            
        # Resolve company context using the service, which validates user relations and company status.
        return resolve_user_company_context(self.request.user, emp_id)
