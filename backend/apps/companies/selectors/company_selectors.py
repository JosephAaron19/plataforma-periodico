from django.db.models import Q
from apps.companies.models.empresa import Empresa
from apps.plans.models.empresa_plan import EmpresaPlan

def get_all_companies_for_admin():
    """
    Returns all non-deleted companies in the system for platform admins.
    Optimized to prevent N+1 queries.
    """
    return Empresa.objects.filter(
        eliminado=False
    ).select_related(
        'creado_por',
        'configuracion',
        'identidad'
    ).prefetch_related(
        'planes_empresa__plan'
    )

def get_authorized_companies_for_user(user):
    """
    Returns only companies where the user has an active relation (UsuarioEmpresa.estado = 'ACTIVO').
    Optimized to prevent N+1 queries.
    """
    return Empresa.objects.filter(
        eliminado=False,
        usuario_empresas__usuario=user,
        usuario_empresas__estado='ACTIVO'
    ).select_related(
        'creado_por',
        'configuracion',
        'identidad'
    ).prefetch_related(
        'planes_empresa__plan'
    ).distinct()

def get_company_active_plan(emp_id):
    """
    Retrieves the currently active EmpresaPlan for the company.
    """
    return EmpresaPlan.objects.filter(
        empresa_id=emp_id,
        estado='ACTIVO'
    ).select_related('plan').first()
