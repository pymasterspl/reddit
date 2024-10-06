from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import models
from django.db.models import Exists, OuterRef, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import (
    AddModeratorForm,
    AdminActionForm,
    CommentForm,
    CommunityForm,
    PostAwardForm,
    PostForm,
    PostReportForm,
    RemoveModeratorForm,
)
from .models import AdminAction, Community, CommunityMember, Post, PostAward, PostReport, PostVote, SavedPost
from .services import handle_admin_action


class PostListView(ListView):
    template_name = "core/post-list.html"
    context_object_name = "posts"

    def get_queryset(self: "PostListView") -> models.QuerySet:
        return Post.objects.filter(parent=None, is_active=True)


@method_decorator(login_required, name="post")
class PostDetailView(DetailView):
    model = Post
    template_name = "core/post-detail.html"
    context_object_name = "post"

    def get_object(self: "Post", queryset: QuerySet[Post] | None = None) -> Post:
        obj = super().get_object(queryset=queryset)
        if not obj.is_active:
            self.template_name = "core/post-inactive.html"
        else:
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
        return reverse_lazy("post-detail", kwargs={"pk": self.object.pk})


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


class PostAwardCreateView(LoginRequiredMixin, CreateView):
    model = PostAward
    form_class = PostAwardForm
    template_name = "core/post-award.html"

    def get_context_data(self: "PostAwardCreateView", **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        context["post"] = post
        return context

    def dispatch(self: "PostAwardCreateView", request: HttpRequest, *args: any, **kwargs: any) -> HttpResponse:
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        user = request.user
        if PostAward.objects.filter(post=post, giver=user).exists():
            messages.error(request, "You've already given an award to this post")
            return redirect("post-detail", pk=post.pk)
        if post.author == request.user:
            messages.error(request, "You cannot give an award to your own post")
            return redirect("post-detail", pk=post.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self: "PostAwardCreateView", form: PostAwardForm) -> HttpResponse:
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        form.instance.giver = self.request.user
        form.instance.receiver = post.author
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self: "PostAwardCreateView") -> str:
        return reverse_lazy("post-detail", kwargs={"pk": self.kwargs["pk"]})


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

    def get_queryset(self: "CommunityListView") -> models.QuerySet:
        user = self.request.user
        return (
            super()
            .get_queryset()
            .prefetch_related("members")
            .annotate(has_access=Exists(CommunityMember.objects.filter(community=OuterRef("pk"), user=user)))
        )

    def get_context_data(self: "CommunityListView", **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        communities = context["communities"]

        for community in communities:
            community.has_access = community.privacy != "30_PRIVATE" or community.has_access

        return context


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
        error_message = "Community does not exist"
        try:
            community = Community.objects.get(slug=self.kwargs["slug"])
        except ObjectDoesNotExist:
            raise Http404(error_message) from None
        if community.privacy == "30_PRIVATE" and not community.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied
        return community

    def get_context_data(self: "CommunityDetailView", **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        community = self.get_object()
        user = self.request.user

        if user.is_authenticated:
            context["is_admin_or_moderator"] = community.is_admin_or_moderator(user)
            if context["is_admin_or_moderator"]:
                context["add_moderator_form"] = AddModeratorForm()
                context["remove_moderator_form"] = RemoveModeratorForm()
        else:
            context["is_admin_or_moderator"] = False

        context["moderators"] = CommunityMember.objects.filter(
            community=community, role=CommunityMember.MODERATOR
        ).select_related("user")
        return context

    def post_add_moderator(self: "CommunityDetailView", request: "HttpRequest", *args: any, **kwargs: any) -> any:
        add_moderator_form = AddModeratorForm(request.POST)
        if add_moderator_form.is_valid():
            user = add_moderator_form.cleaned_data["nickname"]
            self.object.add_moderator(user)
            messages.success(request, f"{user.nickname} is now a moderator of this community.")
        else:
            messages.error(request, "Invalid user or nickname.")
            return self.get(request, *args, **kwargs)

        return redirect("community-detail", slug=self.object.slug)

    def post_remove_moderator(self: "CommunityDetailView", request: "HttpRequest", *args: any, **kwargs: any) -> any:
        remove_moderator_form = RemoveModeratorForm(request.POST)
        if remove_moderator_form.is_valid():
            user = remove_moderator_form.cleaned_data["nickname"]
            if not CommunityMember.objects.filter(
                community=self.object, user=user, role=CommunityMember.MODERATOR
            ).exists():
                messages.error(request, "User is not a moderator of this community.")
                return self.get(request, *args, **kwargs)
            self.object.remove_moderator(user)
            messages.success(request, f"{user.nickname} was successfully removed from moderators.")
        else:
            messages.error(request, "Invalid user or nickname.")
            return self.get(request, *args, **kwargs)

        return redirect("community-detail", slug=self.object.slug)

    def post(self: "CommunityDetailView", request: "HttpRequest", *args: any, **kwargs: any) -> any:
        self.object = self.get_object()
        if not self.object.is_admin_or_moderator(request.user):
            raise PermissionDenied

        action = request.POST.get("action")
        if action == "add_moderator":
            return self.post_add_moderator(request)
        if action == "remove_moderator":
            return self.post_remove_moderator(request)

        messages.error(request, "Invalid action.")
        return self.get(request, *args, **kwargs)


class CommunityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Community
    form_class = CommunityForm
    template_name = "core/community-update.html"

    def test_func(self: "CommunityUpdateView") -> bool:
        community = self.get_object()
        user = self.request.user
        return community.is_admin_or_moderator(user) or community.author == user

    def handle_no_permission(self: "CommunityUpdateView") -> HttpResponse:
        messages.error(self.request, "You do not have permission to update this community.")
        return redirect("community-detail", slug=self.get_object().slug)

    def form_valid(self: "CommunityUpdateView", form: forms.ModelForm) -> HttpResponseRedirect:
        response = super().form_valid(form)
        messages.success(self.request, "Community updated successfully.")
        return response

    def get_success_url(self: "CommunityUpdateView") -> str:
        return reverse_lazy("community-detail", kwargs={"slug": self.object.slug})


class PostReportView(LoginRequiredMixin, CreateView):
    template_name = "core/post-report.html"
    form_class = PostReportForm
    success_url = reverse_lazy("home")
    login_url = "login"

    def form_valid(self: "PostReportView", form: forms.ModelForm) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        report_person = self.request.user
        post_report = form.save(commit=False)
        post_report.post = post
        post_report.report_person = report_person
        post_report.save()
        messages.success(self.request, "Your post has been reported.")
        return super().form_valid(form)

    def get_initial(self: "PostReportView") -> dict[str, Any]:
        initial = super().get_initial()
        initial["post"] = Post.objects.get(pk=self.kwargs["pk"])
        return initial

    def get_form_kwargs(self: "PostReportView") -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs.update({"initial": self.get_initial()})
        return kwargs

    def get_context_data(self: "PostReportView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["post"] = Post.objects.get(pk=self.kwargs["pk"])
        return context


class PostListReportedView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    model = PostReport
    template_name = "core/reported-posts.html"
    context_object_name = "reports"
    paginate_by = 10

    def get_queryset(self: "PostListReportedView") -> QuerySet:
        if not self.request.user.is_staff:
            messages.error(self.request, "You do not have permission to view this page.")
            return redirect("home")
        return PostReport.objects.filter(verified=False)

    def test_func(self: "PostListReportedView") -> bool:
        return self.request.user.is_staff

    def handle_no_permission(self: "PostListReportedView") -> HttpResponse | None:
        if self.request.user.is_authenticated:
            messages.error(self.request, "You do not have permission to view this page.")
            return redirect("home")
        return super().handle_no_permission()


class PostReportedView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    model = PostReport
    template_name = "core/reported-post.html"
    context_object_name = "report"

    def get_queryset(self: "PostReportedView") -> QuerySet:
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            messages.error(self.request, "You do not have permission to view this page.")
            return queryset.none()
        return queryset

    def get_context_data(self: "PostReportedView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        if not hasattr(self, "object"):
            self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["form"] = AdminActionForm()
        return context

    def post(self: "PostReportedView", request: HttpRequest, **kwargs: dict[str, Any]) -> HttpResponse:
        form = AdminActionForm(request.POST)
        report = self.get_object()

        if form.is_valid():
            action: str = form.cleaned_data["action"]
            comment: str = form.cleaned_data["comment"]
            post = report.post
            user = post.author

            admin_action = AdminAction(post_report=report, action=action, comment=comment, performed_by=request.user)
            admin_action.save()

            handle_admin_action(action, report, user, request)
            return redirect(reverse_lazy("post-list-reported"))

        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context)

    def get(self: "PostReportedView", request: HttpRequest, **kwargs: dict[str, Any]) -> HttpResponse:
        self.object = self.get_object()
        if not request.user.is_staff:
            messages.error(request, "You do not have permission to view this page.")
            return redirect("home")
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_object(self: "PostReportedView", queryset: QuerySet | None = None) -> PostReport:
        return super().get_object(queryset)

    def test_func(self: "PostListReportedView") -> bool:
        return self.request.user.is_staff
