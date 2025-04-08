from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models, transaction
from django.db.models import Exists, Max, OuterRef, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from users.models import User

from .forms import (
    AddModeratorForm,
    AdminActionForm,
    CommentForm,
    CommentUpdateForm,
    CommunityForm,
    GroupAdminActionForm,
    PostAwardForm,
    PostForm,
    PostReportForm,
    PostUpdateForm,
    RemoveModeratorForm,
)
from .models import AdminAction, Community, CommunityMember, Post, PostAward, PostReport, PostVote, SavedPost
from .services import handle_admin_action


class PostListView(ListView):
    template_name = "core/post-list.html"
    context_object_name = "posts"

    def get_queryset(self: "PostListView") -> models.QuerySet:
        return Post.objects.filter(parent=None, is_active=True)


class SavedPostListView(LoginRequiredMixin, ListView):
    template_name = "core/post-list-saved.html"
    context_object_name = "posts"

    def get_queryset(self: "SavedPostListView") -> models.QuerySet:
        return Post.objects.filter(
            id__in=SavedPost.objects.filter(user=self.request.user).values("post"), is_active=True
        )


class UserPostListView(LoginRequiredMixin, ListView):
    template_name = "core/user-post-list.html"
    context_object_name = "posts"

    def get_queryset(self: "UserPostListView") -> models.QuerySet:
        user_post = Post.objects.filter(author=self.request.user, parent__isnull=True).order_by("-created_at")
        status = self.request.GET.get("status")
        match status:
            case "draft":
                user_post = user_post.filter(is_draft=True)
            case "archived":
                user_post = user_post.filter(is_archive=True)
            case "published":
                user_post = user_post.filter(is_published=True)
        return user_post


class UserPostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostUpdateForm
    template_name = "core/post-edit.html"
    context_object_name = "posts"

    def get_queryset(self: "UserPostEditView") -> models.QuerySet:
        return Post.objects.filter(author=self.request.user)

    def form_valid(self: "UserPostEditView", form: PostForm) -> HttpResponse:
        if not form.has_changed():
            form.add_error(None, "No changes detected.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self: "UserPostEditView") -> str:
        return reverse_lazy("post-detail", kwargs={"pk": self.object.pk})


class UserCommentEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = CommentUpdateForm
    template_name = "core/comment-edit.html"
    context_object_name = "posts"

    def get_queryset(self: "UserCommentEditView") -> models.QuerySet:
        return Post.objects.filter(author=self.request.user)

    def form_valid(self: "UserCommentEditView", form: CommentUpdateForm) -> HttpResponse:
        if not form.has_changed():
            form.add_error(None, "No changes detected.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self: "UserCommentEditView") -> str:
        return reverse_lazy("post-detail", kwargs={"pk": self.object.parent.pk})


class UserPostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "core/post-delete.html"
    context_object_name = "post"

    def get_queryset(self: "UserPostDeleteView") -> models.QuerySet:
        return Post.objects.filter(author=self.request.user)

    def get_success_url(self: "UserPostDeleteView") -> str:
        return reverse_lazy("user_posts")


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


class CommunityMixin:
    model = Community

    def get_object(self: "CommunityJoin") -> Community:
        error_message = "Community does not exist"
        try:
            community = Community.objects.get(slug=self.kwargs["slug"])
        except ObjectDoesNotExist:
            raise Http404(error_message) from None
        if community.privacy == "30_PRIVATE" and not community.members.filter(id=self.request.user.id).exists():
            error_message = "This will be implemented by add https://app.clickup.com/t/8696fatek"
            raise NotImplementedError(error_message)
        return community


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
            .annotate(has_access=Exists(CommunityMember.objects.filter(community=OuterRef("pk"), user=user.id)))
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


class CommunityJoin(LoginRequiredMixin, CommunityMixin, View):
    model = Community

    @transaction.atomic
    def post(self: "CommunityJoin", request: HttpRequest, slug: str) -> HttpResponseRedirect:
        if request.user in self.get_object().members.all():
            messages.error(request, "You are already a member of this community.")
        else:
            self.get_object().members.add(self.request.user)
            messages.success(request, "You have joined the community!")
        return redirect("community-detail", slug=slug)


class CommunityDetailView(CommunityMixin, DetailView):
    model = Community
    template_name = "core/community-detail.html"
    context_object_name = "community"

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


class ModeratorDashboardView(UserPassesTestMixin, LoginRequiredMixin, TemplateView):
    template_name = "core/moderator_dashboard.html"

    def test_func(self: "ModeratorDashboardView") -> bool:
        return self.request.user.is_staff

    def handle_no_permission(self: "ModeratorDashboardView") -> HttpResponse | None:
        if self.request.user.is_authenticated:
            messages.error(self.request, "You do not have permission to view this page.")
            return redirect("home")
        return super().handle_no_permission()

    def get_context_data(self: "ModeratorDashboardView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["active_posts"] = Post.objects.filter(is_active=True).count()
        if filter_val := self.request.GET.get("author_filter"):
            reported_posts_queryset = PostReport.objects.filter(
                verified=False, post__author__nickname__exact=filter_val
            )
        else:
            reported_posts_queryset = PostReport.objects.filter(verified=False)
        page = self.request.GET.get("page", 1)
        paginator = Paginator(reported_posts_queryset, 10)
        try:
            reported_posts = paginator.page(page)
        except PageNotAnInteger:
            reported_posts = paginator.page(1)
        except EmptyPage:
            reported_posts = paginator.page(paginator.num_pages)
        context["reported_posts"] = reported_posts
        context["reported_posts_count"] = len(reported_posts)
        context["active_users"] = User.objects.filter(is_active=True).count()
        authors = reported_posts_queryset.values_list("post__author__nickname", flat=True).distinct()
        context["authors"] = authors
        context["form"] = GroupAdminActionForm()
        return context

    def post(self: "ModeratorDashboardView", request: HttpRequest) -> HttpResponse:
        form = GroupAdminActionForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid form submission.")
            return redirect("home")

        selected_ids = request.POST.getlist("selected_reports", [])
        reports = PostReport.objects.filter(id__in=selected_ids)
        action = request.POST.get("action_for_selected")
        for report in reports:
            post = report.post
            user = post.author
            admin_action = AdminAction(post_report=report, action=action, performed_by=request.user)
            admin_action.save()
            handle_admin_action(action, report, user, request)
        return redirect("home")


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
            return redirect(reverse_lazy("moderator-dashboard"))

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

    def test_func(self: "PostReportedView") -> bool:
        return self.request.user.is_staff


class UserCommentsListView(LoginRequiredMixin, ListView):
    template_name = "core/user-comments.html"
    context_object_name = "comments"

    def get_queryset(self: "UserCommentsListView") -> QuerySet:
        qs = Post.objects.filter(author=self.request.user, parent__isnull=False).order_by("-created_at")

        filter_val = self.request.GET.get("filter")
        if filter_val and filter_val.startswith("parent-"):
            try:
                parent_id = int(filter_val.split("parent-")[1])
                qs = qs.filter(parent_id=parent_id)
            except (IndexError, ValueError):
                pass

        return qs

    def get_context_data(self: "UserCommentsListView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        parent_ids = (
            Post.objects.filter(author=self.request.user, parent__isnull=False)
            .values_list("parent_id", flat=True)
            .distinct()
        )
        context["parent_posts"] = (
            Post.objects.filter(id__in=parent_ids).exclude(title__isnull=True).exclude(title__exact="")
        )
        return context


class UserVotedListView(LoginRequiredMixin, ListView):
    template_name = "core/user-voted-content.html"
    context_object_name = "posts"
    vote_type = None

    def get_queryset(self: "UserVotedListView") -> models.QuerySet:
        voted_posts = (
            Post.objects.filter(post_votes__user=self.request.user, post_votes__choice=self.vote_type)
            .annotate(post_vote_date=Max("post_votes__updated_at"))
            .order_by("-post_vote_date")
        )

        filter_val = self.request.GET.get("filter")
        match filter_val:
            case "post":
                voted_posts = voted_posts.filter(parent__isnull=True)
            case "comment":
                voted_posts = voted_posts.filter(parent__isnull=False)

        return voted_posts

    def get_context_data(self: "UserVotedListView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["url"] = self.request.resolver_match.url_name
        return context


class UserUpvotedListView(UserVotedListView):
    vote_type = PostVote.UPVOTE


class UserDownvotedListView(UserVotedListView):
    vote_type = PostVote.DOWNVOTE


class UserPublicProfileView(DetailView):
    model = User
    template_name = "core/user-public-profile.html"
    context_object_name = "user"

    def get_object(self: "UserPublicProfileView") -> User:
        return get_object_or_404(User, nickname=self.kwargs["nickname"])

    def get_context_data(self: "UserPublicProfileView", **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context["posts"] = Post.objects.filter(author=user, parent__isnull=True).order_by("-created_at")
        context["previous_url"] = self.request.META.get("HTTP_REFERER")
        return context
