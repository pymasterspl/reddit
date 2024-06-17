from django.urls import path

from .views import AddPostView, PostDetailView, PostListlView

urlpatterns = [
        path("post-list/", PostListlView.as_view(), name="post-list"),
        path("post-detail/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
        path("add-post/", AddPostView.as_view(), name="add-post"),
]
