from django.db import models
from django.utils import timezone
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.models.rol_permiso import RolPermiso
from apps.authorization.constants import EstadoUsuarioEmpresa, EstadoUsuarioEmpresaRol, EstadoRol, EstadoEmpresa

def get_active_user_companies(user):
    """
    Returns a queryset of active companies linked to the user.
    Optimized to select_related the company.
    """
    if not user or not user.is_authenticated:
        return UsuarioEmpresa.objects.none()
    
    return UsuarioEmpresa.objects.using('periodico_db').select_related('empresa').filter(
        usuario=user,
        estado=EstadoUsuarioEmpresa.ACTIVO,
        empresa__estado=EstadoEmpresa.ACTIVA,
        empresa__eliminado=False
    )

def get_user_company_relation(user_id, emp_id):
    """
    Retrieves the UsuarioEmpresa relation if it is active.
    """
    try:
        return UsuarioEmpresa.objects.using('periodico_db').select_related('empresa', 'usuario').get(
            usuario_id=user_id,
            empresa_id=emp_id,
            estado=EstadoUsuarioEmpresa.ACTIVO,
            empresa__estado=EstadoEmpresa.ACTIVA,
            empresa__eliminado=False
        )
    except UsuarioEmpresa.DoesNotExist:
        return None

def get_active_user_company_roles(user_id, emp_id):
    """
    Retrieves all active roles assigned to a user in a given company.
    Optimized with select_related.
    """
    now = timezone.now()
    return UsuarioEmpresaRol.objects.using('periodico_db').select_related('rol').filter(
        usuario_empresa__usuario_id=user_id,
        usuario_empresa__empresa_id=emp_id,
        usuario_empresa__estado=EstadoUsuarioEmpresa.ACTIVO,
        usuario_empresa__empresa__estado=EstadoEmpresa.ACTIVA,
        usuario_empresa__empresa__eliminado=False,
        estado=EstadoUsuarioEmpresaRol.ACTIVO,
        rol__estado=EstadoRol.ACTIVO,
        fecha_inicio__lte=now
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=now)
    )

def get_user_direct_permissions(user_id, emp_id):
    """
    Retrieves all active direct concessions/revocations of permissions for a user in a company.
    """
    now = timezone.now()
    return UsuarioEmpresaPermiso.objects.using('periodico_db').select_related('permiso').filter(
        usuario_empresa__usuario_id=user_id,
        usuario_empresa__empresa_id=emp_id,
        usuario_empresa__estado=EstadoUsuarioEmpresa.ACTIVO,
        usuario_empresa__empresa__estado=EstadoEmpresa.ACTIVA,
        usuario_empresa__empresa__eliminado=False,
        estado=True,
        permiso__estado=EstadoRol.ACTIVO,
        fecha_inicio__lte=now
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=now)
    )
