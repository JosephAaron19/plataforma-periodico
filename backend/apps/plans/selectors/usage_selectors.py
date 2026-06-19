from django.utils import timezone
from django.db.models import Sum
from apps.authorization.models.usuario_empresa import UsuarioEmpresa
from apps.editions.models.edicion import Edicion
from apps.files.models.archivo import Archivo

def get_active_company_members_count(company_id: int) -> int:
    """
    Counts active company members.
    Included states: ACTIVO, PENDIENTE, SUSPENDIDO.
    Excluded states: FINALIZADO.
    """
    return UsuarioEmpresa.objects.using('periodico_db').filter(
        empresa_id=company_id,
        estado__in=['ACTIVO', 'PENDIENTE', 'SUSPENDIDO']
    ).count()

def get_current_month_editions_count(company_id: int) -> int:
    """
    Counts editions created during the current calendar month for the company.
    Excludes deleted editions (eliminado=True).
    """
    now = timezone.now()
    # Beginning of the current calendar month
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    return Edicion.objects.using('periodico_db').filter(
        empresa_id=company_id,
        eliminado=False,
        fecha_creacion__gte=start_of_month
    ).count()

def get_company_storage_bytes(company_id: int) -> int:
    """
    Calculates total storage in bytes consumed by active files of the company.
    Excludes files marked as deleted (eliminado=True).
    """
    result = Archivo.objects.using('periodico_db').filter(
        empresa_id=company_id,
        eliminado=False
    ).aggregate(total_bytes=Sum('tamano_bytes'))
    
    return result.get('total_bytes') or 0
