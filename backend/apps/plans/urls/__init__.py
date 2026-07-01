from django.urls import path
from apps.plans.views import (
    PlanListView, 
    PlanDetailView, 
    PlanAdminListCreateView, 
    PlanAdminDetailUpdateDestroyView,
    PlanPurchaseView,
    ActivatePendingView
)

urlpatterns = [
    path('', PlanListView.as_view(), name='plan-list'),
    path('purchase/', PlanPurchaseView.as_view(), name='plan-purchase'),
    path('activate_pending/', ActivatePendingView.as_view(), name='plan-activate-pending'),
    path('admin/', PlanAdminListCreateView.as_view(), name='plan-admin-list-create'),
    path('admin/<str:plan_code>/', PlanAdminDetailUpdateDestroyView.as_view(), name='plan-admin-detail-update-destroy'),
    path('<str:plan_code>/', PlanDetailView.as_view(), name='plan-detail'),
]

