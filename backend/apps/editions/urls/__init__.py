from django.urls import path
from apps.editions.views import (
    CompanyEditionListCreateView,
    CompanyEditionDetailUpdateView,
    CompanyEditionScheduleView,
    CompanyEditionPublishView,
    CompanyEditionSuspendView,
    CompanyEditionReactivateView,
    PublicEditionListView,
    PublicEditionDetailView
)

urlpatterns = [
    # Administrative endpoints
    path('companies/<int:emp_id>/editions/', CompanyEditionListCreateView.as_view(), name='company-edition-list-create'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/', CompanyEditionDetailUpdateView.as_view(), name='company-edition-detail-update'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/schedule/', CompanyEditionScheduleView.as_view(), name='company-edition-schedule'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/publish/', CompanyEditionPublishView.as_view(), name='company-edition-publish'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/suspend/', CompanyEditionSuspendView.as_view(), name='company-edition-suspend'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/reactivate/', CompanyEditionReactivateView.as_view(), name='company-edition-reactivate'),

    # Public endpoints
    path('public/editions/', PublicEditionListView.as_view(), name='public-edition-list'),
    path('public/editions/<slug:slug>/', PublicEditionDetailView.as_view(), name='public-edition-detail'),
]
