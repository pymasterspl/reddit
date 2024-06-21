from django.urls import path

from .views import PostDetailView, PostListView, PostSaveView, PostVoteView, CommunityCreateView, CommunityDetailView, \
        CommunityListView

urlpatterns = [
        path("post-list/", PostListView.as_view(), name="post-list"),
        path("post-detail/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
        path("post/<int:pk>/vote/<str:vote_type>/", PostVoteView.as_view(), name="post-vote"),
        path("post/<int:pk>/action/<str:action_type>/", PostSaveView.as_view(), name="post-save-unsave"),
        path('communities/', CommunityListView.as_view(), name='community-list'),
        path('community/create/', CommunityCreateView.as_view(), name='community-create'),
        path('community/<slug:slug>/', CommunityDetailView.as_view(), name='community-detail')
]
