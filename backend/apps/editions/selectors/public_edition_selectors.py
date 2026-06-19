from django.utils import timezone
from django.db.models import QuerySet
from apps.editions.models.edicion import Edicion
from apps.editions.constants import EstadoEdicion

def get_public_editions() -> QuerySet[Edicion]:
    """
    Returns a queryset of published editions for active companies.
    - Company must be active (emp_estado='ACTIVA') and not deleted (emp_eliminado=False).
    - Edition must be published (edi_estado='PUBLICADA') and not deleted (edi_eliminado=False).
    - Edition publication date must be reached (edi_fecha_publicacion <= now).
    """
    now = timezone.now()
    return Edicion.objects.using('periodico_db').filter(
        eliminado=False,
        estado=EstadoEdicion.PUBLICADA,
        fecha_publicacion__lte=now,
        empresa__estado='ACTIVA',
        empresa__eliminado=False
    ).select_related('empresa')

def get_public_edition_by_slug(company_slug: str, edition_slug: str) -> Edicion:
    """
    Retrieves a single published, visible edition by company slug and edition slug.
    """
    try:
        return get_public_editions().get(
            empresa__slug=company_slug,
            slug=edition_slug
        )
    except Edicion.DoesNotExist:
        return None
