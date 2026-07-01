from django.urls import path
from apps.content.views.noticia_landing_views import NoticiaLandingListCreateView, NoticiaLandingDetailView

urlpatterns = [
    path('public/news-landing/', NoticiaLandingListCreateView.as_view(), name='public-news-landing-list-create'),
    path('public/news-landing/<int:pk>/', NoticiaLandingDetailView.as_view(), name='public-news-landing-detail'),
]
