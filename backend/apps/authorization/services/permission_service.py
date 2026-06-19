from django.utils import timezone
from django.db import models
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.authorization.models.usuario_empresa_rol import UsuarioEmpresaRol
from apps.authorization.models.usuario_empresa_permiso import UsuarioEmpresaPermiso
from apps.authorization.models.rol_permiso import RolPermiso
from apps.authorization.models.permiso import Permiso
from apps.authorization.constants import (
    EstadoUsuarioEmpresa,
    EstadoUsuarioEmpresaRol,
    EstadoRol,
    EstadoEmpresa,
    TipoRol,
    TipoPermisoDirecto
)
from apps.authorization.selectors.auth_selector import (
    get_user_company_relation,
    get_active_user_company_roles,
    get_user_direct_permissions
)

def is_platform_superadmin(user) -> bool:
    """
    Checks if a user is a global Platform Superadmin.
    A user is a superadmin if they have an active assignment of a rol_tipo='PLATAFORMA'
    and rol_codigo='SUPERADMIN' on any active company-user relation.
    """
    if not user or not user.is_authenticated:
        return False

    now = timezone.now()
    # Check if there is an active uer_usuario_empresa_rol of type PLATAFORMA and code SUPERADMIN
    return UsuarioEmpresaRol.objects.using('periodico_db').filter(
        usuario_empresa__usuario=user,
        usuario_empresa__estado=EstadoUsuarioEmpresa.ACTIVO,
        usuario_empresa__empresa__estado=EstadoEmpresa.ACTIVA,
        usuario_empresa__empresa__eliminado=False,
        estado=EstadoUsuarioEmpresaRol.ACTIVO,
        rol__estado=EstadoRol.ACTIVO,
        rol__tipo=TipoRol.PLATAFORMA,
        rol__codigo='SUPERADMIN',
        fecha_inicio__lte=now
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gt=now)
    ).exists()


def calculate_effective_permissions(user_id, emp_id) -> set[str]:
    """
    Calculates the effective permissions for a user in a company context.
    Precedence Rule: Revocación directa > Concesión directa > Permiso heredado por rol > Sin permiso.
    """
    relation = get_user_company_relation(user_id, emp_id)
    if not relation:
        return set()

    # If the user is a platform superadmin, they get all active permissions in the platform
    if is_platform_superadmin(relation.usuario):
        return set(
            Permiso.objects.using('periodico_db').filter(
                estado=EstadoRol.ACTIVO
            ).values_list('codigo', flat=True)
        )

    # 1. Inherited permissions from active roles
    roles = get_active_user_company_roles(user_id, emp_id)
    role_ids = [r.rol_id for r in roles]
    
    inherited_perms = set()
    if role_ids:
        inherited_perms = set(
            RolPermiso.objects.using('periodico_db').filter(
                rol_id__in=role_ids,
                estado=True,
                permiso__estado=EstadoRol.ACTIVO
            ).values_list('permiso__codigo', flat=True)
        )

    # 2. Direct permissions exceptions (CONCEDER / REVOCAR)
    direct_permissions = get_user_direct_permissions(user_id, emp_id)
    concedidos = set()
    revocados = set()
    
    for dp in direct_permissions:
        if dp.tipo == TipoPermisoDirecto.CONCEDER:
            concedidos.add(dp.permiso.codigo)
        elif dp.tipo == TipoPermisoDirecto.REVOCAR:
            revocados.add(dp.permiso.codigo)

    # Apply precedence rule: (Inherited + Conceded) - Revoked
    effective_permissions = (inherited_perms | concedidos) - revocados
    return effective_permissions
