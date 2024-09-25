from rest_framework.urls import path

from .api_views import CommunitiesAPIList, CommunityDetailAPIView, CommunityPostsListAPIView, PostAPIListView

urlpatterns = [
    path("communities/", CommunitiesAPIList.as_view(), name="api-communities-list"),
    path("communities/<slug:slug>/", CommunityDetailAPIView.as_view(), name="api-community-detail"),
    path("communities/<slug:slug>/posts/", CommunityPostsListAPIView.as_view(), name="api-communities-posts-list"),
    path("posts/", PostAPIListView.as_view(), name="api-posts-list-view"),
]
