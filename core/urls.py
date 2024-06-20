from django.urls import path

from .views import PostDetailView, PostListView, PostSaveView, PostVoteView

urlpatterns = [
        path("post-list/", PostListView.as_view(), name="post-list"),
        path("post-detail/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
        path("post/<int:pk>/vote/<str:vote_type>/", PostVoteView.as_view(), name="post-vote"),
        path("post/<int:pk>/action/<str:action_type>/", PostSaveView.as_view(), name="post-save-unsave"),
]