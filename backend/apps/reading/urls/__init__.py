from django.urls import path
from apps.reading.views import (
    ReadingSessionCreateView,
    ReadingSessionPageView,
    ReadingSessionProgressView,
    PublicSamplePageView
)

urlpatterns = [
    path('editions/<int:edi_id>/reading-session/', ReadingSessionCreateView.as_view(), name='reading-session-create'),
    path('reading-sessions/<uuid:session_id>/pages/<int:page_number>/', ReadingSessionPageView.as_view(), name='reading-session-page'),
    path('reading-sessions/<uuid:session_id>/progress/', ReadingSessionProgressView.as_view(), name='reading-session-progress'),
    path('public/editions/<slug:company_slug>/<slug:edition_slug>/sample/pages/<int:page_number>/', PublicSamplePageView.as_view(), name='public-sample-page'),
]
