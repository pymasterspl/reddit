from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from .forms import AdminActionForm, CommentForm, CommunityForm, PostForm, PostReportForm
from .models import AdminAction, Community, CommunityMember, Post, PostReport, PostVote, SavedPost
from .services import handle_admin_action


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

    def dispatch(
        self: "PostCreateView", request: HttpRequest, *args: tuple[Any], **kwargs: dict[str, Any]
    ) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

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
        return Community.objects.get(slug=self.kwargs["slug"])


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
            return redirect(reverse("post-list-reported"))

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
