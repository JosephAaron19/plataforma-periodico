from apps.authorization.models.rol import Rol
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.constants import EstadoRol, TipoRol

def get_available_company_roles(emp_id: int):
    """
    Returns active company roles. Filters out platform-level roles (PLATFORMA / SUPERADMIN).
    """
    return Rol.objects.using('periodico_db').filter(
        estado=EstadoRol.ACTIVO
    ).exclude(
        tipo=TipoRol.PLATAFORMA
    ).exclude(
        codigo='SUPERADMIN'
    )

def get_member_roles(uep_id: int, emp_id: int):
    """
    Returns all role assignments for a member in a given company.
    """
    return UsuarioEmpresaRol.objects.using('periodico_db').select_related('rol').filter(
        usuario_empresa_id=uep_id,
        usuario_empresa__empresa_id=emp_id
    )
