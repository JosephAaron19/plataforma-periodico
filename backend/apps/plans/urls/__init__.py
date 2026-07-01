from django.urls import path
from apps.plans.views import (
    PlanListView, 
    PlanDetailView, 
    PlanAdminListCreateView, 
    PlanAdminDetailUpdateDestroyView
)

urlpatterns = [
    path('', PlanListView.as_view(), name='plan-list'),
    path('admin/', PlanAdminListCreateView.as_view(), name='plan-admin-list-create'),
    path('admin/<str:plan_code>/', PlanAdminDetailUpdateDestroyView.as_view(), name='plan-admin-detail-update-destroy'),
    path('<str:plan_code>/', PlanDetailView.as_view(), name='plan-detail'),
]
