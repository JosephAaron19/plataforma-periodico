from apps.authorization.models.permiso import Permiso
from apps.authorization.constants import EstadoRol

# Define platform-exclusive permissions to keep them strictly out of company administration scope
PLATFORM_EXCLUSIVE_PERMISSIONS = {
    'EMPRESA_VER',
    'EMPRESA_GESTIONAR',
    'PAGO_SUPERVISAR',
    'CONFIGURACION_GESTIONAR'
}

def get_available_company_permissions(emp_id: int):
    """
    Returns active permissions that are assignable inside the company context.
    Excludes platform-exclusive permissions.
    """
    return Permiso.objects.using('periodico_db').filter(
        estado=EstadoRol.ACTIVO
    ).exclude(
        codigo__in=PLATFORM_EXCLUSIVE_PERMISSIONS
    )
