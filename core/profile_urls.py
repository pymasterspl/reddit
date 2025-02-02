from django.urls import path

from core.views import MyCommentsListView, SavedPostListView, UserPostListView

profile_urlpatterns = [
    path("profile/saved-post-list/", SavedPostListView.as_view(), name="saved_posts"),
    path("profile/my-comments-list", MyCommentsListView.as_view(), name="my_comments"),
    path("profile/posts/", UserPostListView.as_view(), name="user_posts"),
]
