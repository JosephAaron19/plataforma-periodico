from django.urls import path, include
from apps.companies.views import (
    CompanyListCreateView,
    CompanyDetailUpdateView,
    CompanyIdentityView,
    CompanyConfigurationView
)
from apps.plans.views import (
    CompanyPlanDetailView,
    CompanyPlanUsageView,
    CompanyPlanChangeView
)

urlpatterns = [
    path('', CompanyListCreateView.as_view(), name='company-list-create'),
    path('<int:emp_id>/', CompanyDetailUpdateView.as_view(), name='company-detail-update'),
    path('<int:emp_id>/identity/', CompanyIdentityView.as_view(), name='company-identity'),
    path('<int:emp_id>/configuration/', CompanyConfigurationView.as_view(), name='company-configuration'),
    
    # Company Plan routes
    path('<int:emp_id>/plan/', CompanyPlanDetailView.as_view(), name='company-plan-detail'),
    path('<int:emp_id>/plan/usage/', CompanyPlanUsageView.as_view(), name='company-plan-usage'),
    path('<int:emp_id>/plan/change/', CompanyPlanChangeView.as_view(), name='company-plan-change'),

    path('<int:emp_id>/', include('apps.authorization.urls')),
]
