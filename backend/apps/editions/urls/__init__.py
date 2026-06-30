from django.urls import path
from apps.editions.views import (
    CompanyEditionListCreateView,
    CompanyEditionDetailUpdateView,
    CompanyEditionScheduleView,
    CompanyEditionPublishView,
    CompanyEditionSuspendView,
    CompanyEditionReactivateView,
    CompanyEditionNextCodeView,
    CompanyEditionDistributionStatusView,
    CompanyEditionRetryDistributionView,
    PublicEditionListView,
    PublicEditionDetailView,
    ShortNewsListView,
    CompanyEditionPDFView,
    CompanyEditionProcessingStatusView,
    CompanyEditionProcessingRetryView,
    CompanyEditionProcessingCancelView,
    CompanyEditionPageView
)

urlpatterns = [
    # Administrative endpoints
    path('companies/<int:emp_id>/editions/', CompanyEditionListCreateView.as_view(), name='company-edition-list-create'),
    path('companies/<int:emp_id>/editions/next-code/', CompanyEditionNextCodeView.as_view(), name='company-edition-next-code'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/', CompanyEditionDetailUpdateView.as_view(), name='company-edition-detail-update'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/schedule/', CompanyEditionScheduleView.as_view(), name='company-edition-schedule'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/publish/', CompanyEditionPublishView.as_view(), name='company-edition-publish'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/suspend/', CompanyEditionSuspendView.as_view(), name='company-edition-suspend'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/reactivate/', CompanyEditionReactivateView.as_view(), name='company-edition-reactivate'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/pages/<int:page_number>/', CompanyEditionPageView.as_view(), name='company-edition-page'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/distribution-status/', CompanyEditionDistributionStatusView.as_view(), name='company-edition-distribution-status'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/retry-distribution/', CompanyEditionRetryDistributionView.as_view(), name='company-edition-retry-distribution'),

    
    # PDF and Processing endpoints
    path('companies/<int:emp_id>/editions/<int:edi_id>/pdf/', CompanyEditionPDFView.as_view(), name='company-edition-pdf'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/processing/', CompanyEditionProcessingStatusView.as_view(), name='company-edition-processing-status'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/processing/retry/', CompanyEditionProcessingRetryView.as_view(), name='company-edition-processing-retry'),
    path('companies/<int:emp_id>/editions/<int:edi_id>/processing/cancel/', CompanyEditionProcessingCancelView.as_view(), name='company-edition-processing-cancel'),

    # Public endpoints
    path('public/editions/', PublicEditionListView.as_view(), name='public-edition-list'),
    path('public/<slug:company_slug>/editions/<slug:slug>/', PublicEditionDetailView.as_view(), name='public-edition-detail'),
    path('news/short/', ShortNewsListView.as_view(), name='public-news-short'),
]

