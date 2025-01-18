from django.urls import path

from core.views import SavedPostListView

profile_urlpatterns = [
    path("profile/saved-post-list/", SavedPostListView.as_view(), name="saved_posts"),
]
