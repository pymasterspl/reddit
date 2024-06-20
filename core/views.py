from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from .forms import PostForm
from .models import Community, Post


class PostListlView(ListView):

    model = Post
    template_name = "post-list.html"
    context_object_name = "posts"


class PostDetailView(DetailView):

    model = Post
    template_name = "post-detail.html"
    context_object_name = "post"

    def get_object(self: "Post", queryset: QuerySet[Post] | None = None) -> Post:
        obj = super().get_object(queryset=queryset)
        obj.update_display_counter()
        return obj


class AddPostView(CreateView):
    model = Post
    form_class = PostForm
    template_name = "post-add.html"

    def get_form_kwargs(self: "AddPostView") -> dict[str, any]:
        kwargs = super().get_form_kwargs()
        # Set initial community to None
        kwargs["initial"] = {"community": None}
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self: "AddPostView", form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self: "AddPostView", **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["communities"] = Community.objects.filter(is_active=True)
        return context

    def get_success_url(self: "AddPostView") -> str:
        return reverse("post-detail", kwargs={"pk": self.object.pk})
