from django.urls import path
from apps.configuration.views import LandingConfigView

urlpatterns = [
    path('landing/', LandingConfigView.as_view(), name='landing-config'),
]
