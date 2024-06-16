from django.urls import path

from .views import PostDetailView, PostListlView, PostVoteView

urlpatterns = [
        path("post-list/", PostListlView.as_view(), name="post-list"),
        path("post-detail/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
        path("post/<int:pk>/vote/<str:vote_type>/", PostVoteView.as_view(), name="post-vote"),
]
