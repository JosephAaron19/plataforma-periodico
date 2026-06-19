from django.urls import path, include
from apps.companies.views import (
    CompanyListCreateView,
    CompanyDetailUpdateView,
    CompanyIdentityView,
    CompanyConfigurationView
)

urlpatterns = [
    path('', CompanyListCreateView.as_view(), name='company-list-create'),
    path('<int:emp_id>/', CompanyDetailUpdateView.as_view(), name='company-detail-update'),
    path('<int:emp_id>/identity/', CompanyIdentityView.as_view(), name='company-identity'),
    path('<int:emp_id>/configuration/', CompanyConfigurationView.as_view(), name='company-configuration'),
    path('<int:emp_id>/', include('apps.authorization.urls')),
]
