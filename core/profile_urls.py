from django.urls import path

from core.views import SavedPostListView, UserPostListView

profile_urlpatterns = [
    path("profile/saved-post-list/", SavedPostListView.as_view(), name="saved_posts"),
    path("profile/posts/", UserPostListView.as_view(), name="user_posts"),
]
