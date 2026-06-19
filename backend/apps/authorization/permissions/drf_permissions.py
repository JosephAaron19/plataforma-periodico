from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from apps.accounts.constants import EstadoUsuario
from apps.authorization.services.permission_service import is_platform_superadmin, calculate_effective_permissions
from apps.authorization.selectors.auth_selector import get_user_company_relation

class IsAuthenticatedAndActive(BasePermission):
    """
    Allows access only to authenticated, active, verified, and non-deleted users.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        # User must not be deleted, must be active, and must be verified
        return not getattr(user, 'eliminado', False) and getattr(user, 'estado', None) == EstadoUsuario.ACTIVO and getattr(user, 'correo_verificado', False)


class HasCompanyAccess(BasePermission):
    """
    Allows access only if the authenticated user has active access to the resolved company,
    or if the user is a global platform superadmin.
    """
    def get_company_id(self, request, view):
        # Resolve company ID from view route parameter or X-Company-ID header
        emp_id = view.kwargs.get('emp_id')
        if not emp_id:
            emp_id = request.headers.get('X-Company-ID')
        return emp_id

    def has_permission(self, request, view):
        # 1. User must be authenticated and active
        if not IsAuthenticatedAndActive().has_permission(request, view):
            return False
        
        # 2. Resolve company ID
        emp_id = self.get_company_id(request, view)
        if not emp_id:
            return False

        # 3. Superadmins have global platform-wide access
        if is_platform_superadmin(request.user):
            return True

        # 4. Check active relationship
        relation = get_user_company_relation(request.user.id, emp_id)
        if not relation:
            return False
            
        return True


class HasCompanyPermission(HasCompanyAccess):
    """
    Allows access only if the user has the required permission code in their effective permissions.
    """
    def has_permission(self, request, view):
        # 1. Basic access to company
        if not super().has_permission(request, view):
            return False

        # 2. Platform Superadmin has all permissions
        if is_platform_superadmin(request.user):
            return True

        # 3. Extract required permission code from view
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return False

        # 4. Resolve company ID
        emp_id = self.get_company_id(request, view)
        if not emp_id:
            return False

        # 5. Check effective permissions
        effective_perms = calculate_effective_permissions(request.user.id, emp_id)
        return required_permission in effective_perms


class IsPlatformSuperadmin(BasePermission):
    """
    Allows access only to platform superadmins.
    """
    def has_permission(self, request, view):
        if not IsAuthenticatedAndActive().has_permission(request, view):
            return False
        return is_platform_superadmin(request.user)
