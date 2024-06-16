from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Post, PostVote


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


class PostVoteView(LoginRequiredMixin, View):
    def post(self: "PostVoteView", request: HttpRequest, pk: int, vote_type: str) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)
        if vote_type == "up":
            post.vote(request.user, PostVote.UPVOTE)
        elif vote_type == "down":
            post.vote(request.user, PostVote.DOWNVOTE)
        return redirect("post-detail", pk=post.id)
