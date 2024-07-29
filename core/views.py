from typing import Any

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import AddModeratorForm, CommentForm, CommunityForm, PostForm, RemoveModeratorForm
from .models import Community, CommunityMember, Post, PostVote, SavedPost, User


class PostListView(ListView):
    template_name = "core/post-list.html"
    context_object_name = "posts"

    def get_queryset(self: "PostListView") -> models.QuerySet:
        return Post.objects.filter(parent=None)


@method_decorator(login_required, name="post")
class PostDetailView(DetailView):
    model = Post
    template_name = "core/post-detail.html"
    context_object_name = "post"

    def get_object(self: "Post", queryset: QuerySet[Post] | None = None) -> Post:
        obj = super().get_object(queryset=queryset)
        obj.update_display_counter()
        return obj

    def get_context_data(self: "PostDetailView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        comments = self.object.get_comments()

        context["comments"] = comments
        context["form"] = self.object.get_comment_form()
        return context

    def post(self: "PostDetailView", request: HttpRequest, pk: int) -> HttpResponse:
        post = get_object_or_404(Post, id=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            parent_id = form.cleaned_data.get("parent_id")
            content = form.cleaned_data.get("content")
            Post.objects.create(parent_id=parent_id, community=post.community, content=content, author=request.user)
            return redirect(reverse_lazy("post-detail", kwargs={"pk": pk}))

        comments = post.get_comments()
        context = {
            "post": post,
            "comments": comments,
            "form": form,
        }
        html_content = render_to_string(self.template_name, context)
        return HttpResponse(html_content)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "core/post-create.html"
    login_url = "login"

    def get_form_kwargs(self: "PostCreateView") -> dict[str, any]:
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {"community": None}
        return kwargs

    def form_valid(self: "PostCreateView", form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self: "PostCreateView", **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["communities"] = Community.objects.filter(is_active=True)
        return context

    def get_success_url(self: "PostCreateView") -> str:
        return reverse("post-detail", kwargs={"pk": self.object.pk})


class PostVoteView(LoginRequiredMixin, View):
    def post(self: "PostVoteView", request: HttpRequest, pk: int, vote_type: str) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)
        if vote_type == "up":
            post.vote(request.user, PostVote.UPVOTE)
        elif vote_type == "down":
            post.vote(request.user, PostVote.DOWNVOTE)

        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("post-detail", pk=post.id)


class PostSaveView(LoginRequiredMixin, View):
    def post(self: "PostSaveView", request: HttpRequest, pk: int, action_type: str) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)
        if action_type == "save":
            SavedPost.save_post(user=self.request.user, post=post)
        elif action_type == "unsave":
            SavedPost.remove_saved_post(user=self.request.user, post=post)

        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("post-detail", pk=post.id)


class CommunityListView(ListView):
    model = Community
    template_name = "core/community-list.html"
    context_object_name = "communities"
    paginate_by = 10


class CommunityCreateView(LoginRequiredMixin, CreateView):
    model = Community
    form_class = CommunityForm
    template_name = "core/community-create.html"

    def form_valid(self: "CommunityCreateView", form: forms.ModelForm) -> HttpResponseRedirect:
        form.instance.author = self.request.user
        response = super().form_valid(form)
        CommunityMember.objects.create(
            community=self.object,
            user=self.request.user,
            role=CommunityMember.ADMIN,
        )
        return response

    def get_success_url(self: "CommunityCreateView") -> str:
        return reverse_lazy("community-detail", kwargs={"slug": self.object.slug})


class CommunityDetailView(DetailView):
    model = Community
    template_name = "core/community-detail.html"
    context_object_name = "community"

    def get_object(self: "CommunityDetailView") -> Community:
        community = Community.objects.get(slug=self.kwargs["slug"])
        if community.privacy == "PRIVATE" and not community.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied
        return community

    def get_context_data(self: "CommunityDetailView", **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        community = self.get_object()
        user = self.request.user

        if user.is_authenticated:
            context["is_admin_or_moderator"] = community.is_admin_or_moderator(user)
        else:
            context["is_admin_or_moderator"] = False

        context["add_moderator_form"] = AddModeratorForm()
        context["remove_moderator_form"] = RemoveModeratorForm()
        context["moderators"] = CommunityMember.objects.filter(
            community=community, role=CommunityMember.MODERATOR
        ).select_related("user")
        return context

    def post(self: "CommunityDetailView", request: "HttpRequest", *args: any, **kwargs: any) -> any: # noqa: ARG002
        self.object = self.get_object()
        try:
            if not self.object.is_admin_or_moderator(request.user):
                raise PermissionDenied

            add_moderator_form = AddModeratorForm(request.POST)
            remove_moderator_form = RemoveModeratorForm(request.POST)

            if "add_moderator" in request.POST and add_moderator_form.is_valid():
                user = get_object_or_404(User, nickname=add_moderator_form.cleaned_data["nickname"])
                self.object.add_moderator(user)

            if "remove_moderator" in request.POST and remove_moderator_form.is_valid():
                user = get_object_or_404(User, nickname=remove_moderator_form.cleaned_data["nickname"])
                self.object.remove_moderator(user)

            return redirect("community-detail", slug=self.object.slug)

        except PermissionError as e:
            return HttpResponse(str(e), status=403)


class CommunityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Community
    form_class = CommunityForm
    template_name = "core/community-update.html"

    def test_func(self: "CommunityUpdateView") -> bool:
        community = self.get_object()
        user = self.request.user
        is_author = community.author == user
        user_role = CommunityMember.objects.filter(community=community, user=user).first()

        if is_author:
            return True

        if user_role:
            return user_role.role in [CommunityMember.ADMIN, CommunityMember.MODERATOR]

        return False

    def get_success_url(self: "CommunityUpdateView") -> str:
        return reverse_lazy("community-detail", kwargs={"slug": self.object.slug})
