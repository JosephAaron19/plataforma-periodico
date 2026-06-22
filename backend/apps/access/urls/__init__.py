from django.urls import path
from apps.access.views.library_views import LibraryListView

urlpatterns = [
    path('library/', LibraryListView.as_view(), name='library-list'),
]
