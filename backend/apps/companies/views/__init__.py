from apps.companies.views.companies import CompanyListCreateView, CompanyDetailUpdateView
from apps.companies.views.identity import CompanyIdentityView
from apps.companies.views.configuration import CompanyConfigurationView

__all__ = [
    'CompanyListCreateView',
    'CompanyDetailUpdateView',
    'CompanyIdentityView',
    'CompanyConfigurationView'
]
