from django.urls import path
from apps.plans.views import PlanListView, PlanDetailView

urlpatterns = [
    path('', PlanListView.as_view(), name='plan-list'),
    path('<str:plan_code>/', PlanDetailView.as_view(), name='plan-detail'),
]
