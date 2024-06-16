from django.db.models import QuerySet
from django.views.generic import DetailView, ListView

from .models import Post


class PostListlView(ListView):

    """Provide a temporary view for internal testing of the post view count feature.

    This view is not intended for production use and should be accessed only by developers.
    """

    model = Post
    template_name = "post-list.html"
    context_object_name = "posts"


class PostDetailView(DetailView):

    """Provide a temporary view for internal testing of the post view count feature.

    This view is not intended for production use and should be accessed only by developers.
    """

    model = Post
    template_name = "post-detail.html"
    context_object_name = "post"

    def get_object(self: "Post", queryset: QuerySet[Post] | None = None) -> Post:
        obj = super().get_object(queryset=queryset)
        obj.update_display_counter()
        return obj
