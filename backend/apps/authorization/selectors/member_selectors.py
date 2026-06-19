from apps.authorization.models.usuario_empresa import UsuarioEmpresa

def get_company_members_queryset(emp_id):
    """
    Returns a pre-fetched and optimized queryset of all member relationships 
    for the specified company.
    """
    qs = UsuarioEmpresa.objects.using('periodico_db').filter(
        empresa_id=emp_id
    ).select_related(
        'usuario', 
        'asignado_por'
    ).prefetch_related(
        'roles_asignados__rol'
    )
    qs.order_like_distinct = False  # Django meta helper if needed
    return qs
