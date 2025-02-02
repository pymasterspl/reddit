from django.urls import path

from core.views import SavedPostListView, UserCommentsListView, UserPostListView

profile_urlpatterns = [
    path("profile/saved-post-list/", SavedPostListView.as_view(), name="saved_posts"),
    path("profile/user-comments-list", UserCommentsListView.as_view(), name="user_comments"),
    path("profile/posts/", UserPostListView.as_view(), name="user_posts"),
]
