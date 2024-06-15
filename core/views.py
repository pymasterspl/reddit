from django.shortcuts import get_object_or_404
from django.views.generic import ListView, TemplateView

from .models import Post


class PostListlView(ListView):

    """This view is temporary and used for internal testing of the post view count feature.
    It is not intended for production use and should be accessed only by developers.
    """

    model = Post
    template_name = "post-list.html"
    context_object_name = "posts"


class PostDetailView(TemplateView):

    """This view is temporary and used for internal testing of the post view count feature.
    It is not intended for production use and should be accessed only by developers.
    """

    template_name = "post-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        post_id = self.kwargs.get("pk")
        post = get_object_or_404(Post, pk=post_id)
        post.view_count += 1
        post.save(update_fields=["view_count"], skip_version_check=True)

        context["post"] = post
        context["post_id"] = post_id

        return context
