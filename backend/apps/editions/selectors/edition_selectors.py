from django.db.models import QuerySet
from apps.editions.models.edicion import Edicion

def get_company_editions(company_id: int) -> QuerySet[Edicion]:
    """
    Returns a base queryset for all active (non-deleted) editions belonging to a company.
    """
    return Edicion.objects.using('periodico_db').filter(
        empresa_id=company_id,
        eliminado=False
    )

def get_company_edition_by_id(company_id: int, edition_id: int) -> Edicion:
    """
    Retrieves a single active edition belonging to a company, or None if it doesn't exist.
    """
    try:
        return get_company_editions(company_id).get(id=edition_id)
    except Edicion.DoesNotExist:
        return None

def get_company_edition_by_slug(company_id: int, slug: str) -> Edicion:
    """
    Retrieves a single active edition belonging to a company by its slug, or None if it doesn't exist.
    """
    try:
        return get_company_editions(company_id).get(slug=slug)
    except Edicion.DoesNotExist:
        return None
