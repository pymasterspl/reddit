from django.urls import path

from core.views import SavedPostListView, UserPostDeleteView, UserPostEditView, UserPostListView

profile_urlpatterns = [
    path("profile/saved-post-list/", SavedPostListView.as_view(), name="saved_posts"),
    path("profile/posts/", UserPostListView.as_view(), name="user_posts"),
    path("profile/posts/edit/<int:pk>/", UserPostEditView.as_view(), name="edit_post"),
    path("profile/posts/delete/<int:pk>/", UserPostDeleteView.as_view(), name="delete_post"),
]
