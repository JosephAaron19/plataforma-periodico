from django.urls import path
from apps.access.views.library_views import LibraryListView, UserAssignedEditionsListView

urlpatterns = [
    path('library/', LibraryListView.as_view(), name='library-list'),
    path('users/<int:user_id>/editions/', UserAssignedEditionsListView.as_view(), name='user-assigned-editions'),
]
