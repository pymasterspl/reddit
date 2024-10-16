from django.urls import include, path

from .views import (
    CommunityCreateView,
    CommunityDetailView,
    CommunityListView,
    CommunityUpdateView,
    PostAwardCreateView,
    PostCreateView,
    PostDetailView,
    PostListReportedView,
    PostListView,
    PostReportedView,
    PostReportView,
    PostSaveView,
    PostVoteView,
)

urlpatterns = [
    path("post-list/", PostListView.as_view(), name="post-list"),
    path("post-detail/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
    path("post-create/", PostCreateView.as_view(), name="post-create"),
    path("post/<int:pk>/vote/<str:vote_type>/", PostVoteView.as_view(), name="post-vote"),
    path("post/<int:pk>/award/", PostAwardCreateView.as_view(), name="post-award"),
    path("post/<int:pk>/action/<str:action_type>/", PostSaveView.as_view(), name="post-save-unsave"),
    path("communities/", CommunityListView.as_view(), name="community-list"),
    path("community/create/", CommunityCreateView.as_view(), name="community-create"),
    path("community/<slug:slug>/", CommunityDetailView.as_view(), name="community-detail"),
    path("post/report/<int:pk>/", PostReportView.as_view(), name="post-report"),
    path("reported-posts/", PostListReportedView.as_view(), name="post-list-reported"),
    path("reported-post/<int:pk>/", PostReportedView.as_view(), name="reported-post"),
    path("community/<slug:slug>/update/", CommunityUpdateView.as_view(), name="community-update"),
    path("api/", include("core.api_urls")),
]
