from django.urls import path

from core.views import (
    SavedPostListView,
    UserCommentsListView,
    UserDownvotedListView,
    UserPostListView,
    UserPublicProfileView,
    UserUpvotedListView,
)

profile_urlpatterns = [
    path("profile/saved-posts/", SavedPostListView.as_view(), name="saved_posts"),
    path("profile/comments/", UserCommentsListView.as_view(), name="user_comments"),
    path("profile/posts/", UserPostListView.as_view(), name="user_posts"),
    path("profile/upvoted/", UserUpvotedListView.as_view(), name="user_upvoted"),
    path("profile/downvoted/", UserDownvotedListView.as_view(), name="user_downvoted"),
    path("profile/<str:nickname>/", UserPublicProfileView.as_view(), name="user_public_profile"),
]
