import io
from pathlib import Path

import pytest
from django.conf import Settings, settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse, reverse_lazy
from faker import Faker
from PIL import Image

from core.models import Community, CommunityMember, Post, PostReport

from .test_utils import generate_random_password

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture()
def user(client: Client) -> User:
    password = generate_random_password()
    user = User.objects.create_user(
        email="test_user@example.com",
        nickname="TestUser",
        password=password,
    )

    client.login(email=user.email, password=user.password)
    user.plain_password = password
    return user


@pytest.fixture()
def admin(client: Client) -> User:
    password = generate_random_password()
    user = User.objects.create_user(
        email="test_admin@example.com", nickname="TestAdmin", password=password, is_superuser=True, is_staff=True
    )

    client.login(email=user.email, password=user.password)
    return user


@pytest.fixture()
def user_with_avatar(client: Client, create_avatar: SimpleUploadedFile) -> User:
    password = generate_random_password()
    user = User.objects.create_user(
        email="test_user@example.com",
        nickname="TestUser",
        password=password,
    )
    user.profile.avatar = create_avatar
    user.save()
    user.profile.save()
    client.login(email=user.email, password=user.password)

    return user


@pytest.fixture()
def create_avatar() -> SimpleUploadedFile:
    avatar_dir = Path(settings.MEDIA_ROOT) / "users_avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)
    base_filename = "test_avatar"

    avatar_path = Path(f"{avatar_dir}/{base_filename}.jpg")

    with Path.open(avatar_path, "wb") as f:
        f.write(img_io.read())

    with Path.open(avatar_path, "rb") as f:
        avatar = SimpleUploadedFile(name=avatar_path, content=f.read(), content_type="image/jpeg")

    yield avatar

    for file_path in avatar_dir.glob(f"{base_filename}*"):
        if Path.exists(file_path):
            Path.unlink(file_path)


@pytest.fixture()
def inactive_post(community: Community) -> Post:
    return Post.objects.create(
        title="Inactive Post", content="Other content", is_active=False, community_id=community.id
    )


@pytest.fixture()
def community() -> Community:
    return Community.objects.create(name="Test Community", is_active=True)


@pytest.fixture()
def report_data() -> dict[str, str]:
    def _create_report_data(report_type: str = "20_EU_ILLEGAL_CONTENT") -> dict[str, str]:
        fake = Faker()
        return {
            "report_type": report_type,
            "report_details": fake.text(),
        }

    return _create_report_data


@pytest.fixture()
def post_report(post: Post, user: User) -> PostReport:
    fake = Faker()
    return PostReport.objects.create(
        post=post,
        report_type="THREATENING_VIOLENCE",
        verified=True,
        report_details=fake.text(max_nb_chars=100),
        report_person=user,
    )


@pytest.fixture()
def unverified_post_report(post: Post, user: User) -> PostReport:
    return PostReport.objects.create(post=post, verified=False, report_person=user)


@pytest.fixture()
def admin_action_form_data() -> dict:
    return {"action": "20_DELETE", "comment": "This post violates the guidelines."}


@pytest.fixture()
def default_avatar_url(settings: Settings) -> None:
    return settings.DEFAULT_AVATAR_URL


@pytest.fixture()
def restricted_community(user: User) -> Community:
    return Community.objects.create(name="Restricted Community", is_active=True, author=user)


@pytest.fixture()
def comment(post: Post, community: Community, user: User) -> Post:
    return Post.objects.create(
        parent_id=post.pk, community=community, author=user, content="This is a test comment content."
    )


def test_add_post_valid(client: Client, user: User, community: Community) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    client.force_login(user)
    response = client.post(reverse("post-create"), data=data, follow=True)
    assert response.status_code == 200
    assert response.context["post"].author == user
    assert response.context["post"].title == data["title"]
    assert response.context["post"].content == data["content"]


def test_add_post_invalid(client: Client, user: User, community: Community) -> None:
    data = {"title": ""}
    client.force_login(user)
    response = client.post(reverse("post-create"), data=data)
    assert response.status_code == 200
    form = response.context["form"]
    assert "This field is required." in form.errors["title"]
    assert "This field is required." in form.errors["content"]


def test_add_post_unauthorized(client: Client, community: Community) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    response = client.post(reverse("post-create"), data=data)
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_report_post(client: Client, user: User, post: Post, report_data: dict) -> None:
    data = report_data()
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert str(messages[0]) == "Your post has been reported."


def test_report_post_invalid_data(client: Client, user: User, post: Post) -> None:
    client.force_login(user)
    invalid_data = {}
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=invalid_data)
    assert "form" in response.context, "Form is not present in the response context"
    form = response.context["form"]
    assert len(form.errors) > 0, "There should be at least one form error"


def test_report_post_unauthorized(client: Client, post: Post, report_data: dict) -> None:
    data = report_data()
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    assert str(reverse_lazy("login")) in response.url


def test_add_comment_valid(client: Client, user: User, post: Post) -> None:
    data = {
        "parent_id": post.pk,
        "content": "This is a test comment content.",
    }
    client.force_login(user)
    assert post.children_count == 0
    assert post.get_comments().count() == 0
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data, follow=True)
    assert response.status_code == 200
    assert post.children_count == 1
    assert post.get_comments().count() == 1
    post.refresh_from_db()
    assert response.context["comments"][0].author == user
    assert response.context["comments"][0].content == data["content"]


def test_add_comment_invalid(client: Client, user: User, post: Post) -> None:
    data = {"parent_id": post.pk, "content": ""}
    client.force_login(user)
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 200
    form = response.context["form"]
    assert len(form.errors) == 1
    assert "This field is required." in form.errors["content"]


def test_add_comment_valid_special_characters(client: Client, user: User, post: Post) -> None:
    data = {"parent_id": post.pk, "content": "This is a test comment with special characters! 😊🚀✨"}
    client.force_login(user)
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data, follow=True)
    assert response.status_code == 200
    new_comment = Post.objects.get(content=data["content"])
    assert new_comment.content == data["content"]


def test_add_comment_unauthorized(client: Client, post: Post) -> None:
    data = {
        "parent_id": post.pk,
        "content": "This is a test comment content.",
    }
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_reported_detail_post_by_user(client: Client, user: User, post: Post, report_data: dict) -> None:
    data = report_data()
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    client.force_login(user)
    response = client.get(reverse("reported-post", kwargs={"pk": post.pk}))
    assert response.status_code == 403
    assert "You don't have access to this community." in response.content.decode()


def test_reported_detail_post_by_anonymous_user(client: Client, post_report: PostReport) -> None:
    response = client.get(reverse("post-report", kwargs={"pk": post_report.pk}))
    assert response.status_code == 302
    assert f"{settings.LOGIN_URL}?next={reverse('post-report', kwargs={'pk': post_report.pk})}" in response.url


def test_add_nested_comment_valid(client: Client, user: User, post: Post, comment: Post) -> None:
    data = {
        "parent_id": comment.pk,
        "content": "This is a test nested comment content.",
    }
    client.force_login(user)
    assert post.children_count == 1
    assert post.get_comments().count() == 1
    assert comment.children_count == 0
    assert comment.get_comments().count() == 0
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data, follow=True)
    assert response.status_code == 200
    post.refresh_from_db()
    comment.refresh_from_db()
    assert post.children_count == 2
    assert post.get_comments().count() == 1
    assert comment.children_count == 1
    assert comment.get_comments().count() == 1

    new_comment = Post.objects.get(content=data["content"])
    assert new_comment.author == user
    assert new_comment.parent == comment


def test_add_nested_comment_invalid(client: Client, user: User, post: Post, comment: Post) -> None:
    data = {"parent_id": comment.pk, "content": ""}
    client.force_login(user)
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 200
    form = response.context["form"]
    assert len(form.errors) == 1
    assert "This field is required." in form.errors["content"]


def test_add_nested_comment_unauthorized(client: Client, post: Post, comment: Post) -> None:
    data = {
        "parent_id": comment.pk,
        "content": "This is a test nested comment content.",
    }
    response = client.post(reverse("post-detail", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_add_deeply_nested_comment_valid(client: Client, user: User, post: Post) -> None:
    client.force_login(user)
    parent_comment = post
    for _ in range(10):
        response = client.post(
            reverse("post-detail", kwargs={"pk": post.pk}),
            data={"parent_id": parent_comment.pk, "content": "Nested comment"},
            follow=True,
        )
        assert response.status_code == 200
        parent_comment = Post.objects.latest("pk")

    post.refresh_from_db()
    assert post.children_count == 10
    assert parent_comment.children_count == 0
    assert parent_comment.parent.children_count == 1


@pytest.mark.django_db()
def test_post_user_avatar_display(client: Client, community: Community, user_with_avatar: User) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    client.force_login(user_with_avatar)
    response = client.post(reverse("post-create"), data=data, follow=True)
    post = response.context["post"]
    assert post.author.profile.avatar_url == user_with_avatar.profile.avatar_url


@pytest.mark.django_db()
def test_post_user_without_avatar(
    client: Client, community: Community, another_user: User, default_avatar_url: str
) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    client.force_login(another_user)
    response = client.post(reverse("post-create"), data=data, follow=True)
    assert Post.objects.count() == 1
    assert "form" in response.context
    form = response.context["form"]
    assert form.errors == {}
    post = Post.objects.first()
    assert post.author.profile.avatar_url == default_avatar_url


def test_restricted_community_access(client: Client, restricted_community: Community, user: User) -> None:
    client.force_login(user)
    response = client.get(reverse("community-detail", kwargs={"slug": restricted_community.slug}))
    assert response.status_code == 200


def test_community_view(client: Client, community: Community) -> None:
    response = client.get(reverse("community-list"))
    assert response.status_code == 200
    assert len(response.context["communities"]) == 1


def test_create_community_view(client: Client, user: User) -> None:
    client.force_login(user)
    url = reverse("community-create")
    valid_data = {"name": "Test Community", "privacy": "10_PUBLIC", "is_18_plus": True}
    response = client.post(url, valid_data)
    assert response.status_code == 302
    assert Community.objects.filter(name="Test Community").exists()

    invalid_data = {"name": "", "privacy": "INVALID", "is_18_plus": "not_boolean"}
    response = client.post(url, invalid_data)
    assert response.status_code == 200
    assert "form" in response.context
    assert len(response.context["form"].errors) == 2
    assert "This field is required." in response.context["form"].errors["name"]
    assert (
        "Select a valid choice. INVALID is not one of the available choices."
        in response.context["form"].errors["privacy"]
    )


def test_join_community_success(client: Client, user: User, community: Community) -> None:
    """Test that a user can successfully join a community."""
    client.force_login(user)
    url = reverse("community-join", kwargs={"slug": community.slug})
    response = client.post(url)

    messages = list(get_messages(response.wsgi_request))
    assert response.status_code == 302
    assert any("You have joined the community!" in message.message for message in messages)


def test_join_already_member(client: Client, user: User, community: Community) -> None:
    """Test that a user is notified if they are already a member of the community."""
    client.force_login(user)
    url = reverse("community-join", kwargs={"slug": community.slug})
    client.post(url)  # First join to become a member

    # Attempt to join again
    response = client.post(url)
    messages = list(get_messages(response.wsgi_request))
    assert response.status_code == 302
    assert any("You are already a member of this community." in message.message for message in messages)


def test_join_non_existent_community(client: Client, user: User) -> None:
    """Test that attempting to join a non-existent community returns a 404 error."""
    client.force_login(user)
    url = reverse("community-join", kwargs={"slug": "not_exist"})
    response = client.post(url)

    assert response.status_code == 404
    assert "Community does not exist" in str(response.context)


def test_community_detail_view(client: Client, user: User, community: Community) -> None:
    client.force_login(user)
    url = reverse("community-detail", kwargs={"slug": community.slug})
    response = client.get(url)

    assert response.status_code == 200
    assert "community" in response.context
    assert response.context["community"] == community


def test_community_detail_view_not_found(client: Client, user: User) -> None:
    client.force_login(user)
    url = reverse("community-detail", kwargs={"slug": "non-existent"})
    response = client.get(url)
    assert response.status_code == 404


def test_update_community_view_without_permission(
    client: Client, non_authored_community: Community, user: User
) -> None:
    client.force_login(user)
    community = non_authored_community
    response = client.post(reverse("community-update", kwargs={"slug": community.slug}), {"name": "Updated Community"})
    assert response.status_code == 302
    assert response.url == reverse("community-detail", kwargs={"slug": community.slug})
    response = client.get(response.url)
    assert "You do not have permission to update this community." in response.content.decode()
    community.refresh_from_db()
    assert community.name == "Test Community"


def test_add_moderator(client: Client, community: Community, user: User) -> None:
    admin_password = generate_random_password()

    admin = User.objects.create_user(email="admin@example.com", password=admin_password, nickname="adminnick")

    client.force_login(admin)
    CommunityMember.objects.create(community=community, user=admin, role=CommunityMember.ADMIN)

    url = reverse("community-detail", kwargs={"slug": community.slug})
    form_data = {"nickname": user.nickname}

    response = client.post(url, {"action": "add_moderator", **form_data})
    assert response.status_code == 302

    community.refresh_from_db()
    assert CommunityMember.objects.filter(community=community, user=user, role=CommunityMember.MODERATOR).exists()


def test_remove_moderator(client: Client, user: User, community: Community) -> None:
    admin_password = generate_random_password()

    admin = User.objects.create_user(email="admin@example.com", password=admin_password, nickname="adminnick")

    client.force_login(admin)
    CommunityMember.objects.create(community=community, user=admin, role=CommunityMember.ADMIN)
    CommunityMember.objects.create(community=community, user=user, role=CommunityMember.MODERATOR)

    url = reverse("community-detail", kwargs={"slug": community.slug})
    form_data = {"nickname": user.nickname}

    response = client.post(url, {"action": "remove_moderator", **form_data})
    assert response.status_code == 302

    assert not CommunityMember.objects.filter(community=community, user=user, role=CommunityMember.MODERATOR).exists()


def test_report_post_breaks_rules(client: Client, user: User, post: Post, report_data: dict) -> None:
    data = report_data("10_BREAKS_RULES")
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert str(messages[0]) == "Your post has been reported."


def test_report_post_harassment(client: Client, user: User, post: Post, report_data: dict) -> None:
    data = report_data("30_HARASSMENT")
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert str(messages[0]) == "Your post has been reported."


def test_add_non_existing_moderator(client: Client, community: Community, user: User) -> None:
    admin_password = generate_random_password()

    admin = User.objects.create_user(email="admin@example.com", password=admin_password, nickname="adminnick")

    client.force_login(admin)
    CommunityMember.objects.create(community=community, user=admin, role=CommunityMember.ADMIN)

    url = reverse("community-detail", kwargs={"slug": community.slug})
    form_data = {"nickname": "nonexistentuser"}

    response = client.post(url, {"action": "add_moderator", **form_data})
    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert any("Invalid user or nickname." in message.message for message in messages)


def test_remove_non_existing_moderator(client: Client, community: Community, user: User) -> None:
    admin_password = generate_random_password()

    admin = User.objects.create_user(email="admin@example.com", password=admin_password, nickname="adminnick")

    client.force_login(admin)
    CommunityMember.objects.create(community=community, user=admin, role=CommunityMember.ADMIN)

    url = reverse("community-detail", kwargs={"slug": community.slug})
    form_data = {"nickname": user.nickname}

    response = client.post(url, {"action": "remove_moderator", **form_data})
    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert any("User is not a moderator of this community." in message.message for message in messages)


def test_fetch_saved_post_valid(client: Client, user: User, post: Post, community: Community) -> None:
    data = {
        "community": community.pk,
        "title": "Test Post Title",
        "content": "This is a test post content.",
    }
    client.force_login(user)
    client.post(reverse("post-create"), data=data, follow=True)
    client.post(reverse("post-save-unsave", kwargs={"pk": post.pk, "action_type": "save"}))
    response = client.get(reverse("saved_posts"))
    assert response.status_code == 200
    assert len(response.context_data["posts"]) == 1


def test_fetch_empty_list_of_saved_post_valid(client: Client, user: User, post: Post, community: Community) -> None:
    client.force_login(user)
    client.post(reverse("post-save-unsave", kwargs={"pk": post.pk, "action_type": "save"}))
    client.post(reverse("post-save-unsave", kwargs={"pk": post.pk, "action_type": "unsave"}))
    response = client.get(reverse("saved_posts"))
    assert len(response.context_data["posts"]) == 0


def test_fetch_user_comments_valid(client: Client, user: User, comment: Post) -> None:
    client.force_login(user)
    response = client.get(reverse("user_comments"))
    assert response.status_code == 200
    assert len(response.context_data["comments"]) == 1


def test_fetch_empty_list_no_comments_exist(client: Client, user: User) -> None:
    client.force_login(user)
    response = client.get(reverse("user_comments"))
    assert response.status_code == 200
    assert len(response.context_data["comments"]) == 0


def test_fetch_empty_list_other_user_comments_exist(
    client: Client, another_user: User, post: Post, comment: Post
) -> None:
    client.force_login(another_user)
    response = client.get(reverse("user_comments"))
    assert response.status_code == 200
    assert len(response.context_data["comments"]) == 0


def test_fetch_user_comments_with_valid_parent_filter(
    client: Client, user: User, post: Post, community: Community
) -> None:
    comment1 = Post.objects.create(author=user, content="Test comment 1", parent=post, community=community)
    other_post = Post.objects.create(author=user, content="Test post 2", community=community)
    Post.objects.create(author=user, content="Test comment 2", parent=other_post, community=community)
    client.force_login(user)
    response = client.get(f"{reverse('user_comments')}?filter=parent-{post.id}")
    assert response.status_code == 200
    assert len(response.context_data["comments"]) == 1
    assert response.context_data["comments"][0] == comment1


def test_fetch_user_comments_with_invalid_parent_filter(client: Client, user: User, comment: Post) -> None:
    client.force_login(user)
    response = client.get(f"{reverse('user_comments')}?filter=parent-99999")
    assert response.status_code == 200
    assert len(response.context_data["comments"]) == 0


def test_fetch_user_comments_with_empty_filter(client: Client, user: User, comment: Post) -> None:
    client.force_login(user)
    response = client.get(f"{reverse('user_comments')}?filter=")
    assert response.status_code == 200
    assert len(response.context_data["comments"]) == 1


def test_edit_comment_valid(client: Client, user: User, post: Post, comment: Post) -> None:
    client.force_login(user)
    edit_response = client.post(reverse("edit_comment", kwargs={"pk": comment.pk}), data={"content": "TEST"})
    assert edit_response.status_code == 302
    response = client.get(reverse("post-detail", kwargs={"pk": comment.pk}))
    assert response.context["post"].content == "TEST"


def test_edit_comment_empty_content_invalid(client: Client, user: User, post: Post, comment: Post) -> None:
    client.force_login(user)
    edit_response = client.post(reverse("edit_comment", kwargs={"pk": comment.pk}), data={"content": ""})
    assert edit_response.status_code == 200
    assert edit_response.context_data["form"].errors == {"content": ["This field is required."]}


def test_moderator_dashboard_view_staff(
    client: Client, admin: User, inactive_post: Post, unverified_post_report: PostReport, post_report: PostReport
) -> None:
    client.force_login(admin)
    url = reverse("moderator-dashboard")
    response = client.get(url)
    assert response.status_code == 200

    active_posts_count = Post.objects.filter(is_active=True).count()
    expected_reported_posts = list(PostReport.objects.filter(verified=False))
    reported_posts_count = len(expected_reported_posts)
    active_users_count = User.objects.filter(is_active=True).count()

    assert response.context["active_posts"] == active_posts_count

    reported_posts_context = list(response.context["reported_posts"])
    assert len(reported_posts_context) == reported_posts_count
    for report in reported_posts_context:
        assert report.verified is False

    assert response.context["active_users"] == active_users_count


def test_moderator_dashboard_view_non_staff(client: Client, user: User) -> None:
    client.force_login(user)
    url = reverse("moderator-dashboard")
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse("home")
    messages = list(get_messages(response.wsgi_request))
    assert any("You do not have permission to view this page." in m.message for m in messages)


def test_moderator_dashboard_view_anonymous(client: Client) -> None:
    url = reverse("moderator-dashboard")
    response = client.get(url)
    assert response.status_code == 302
    expected_url = f"{reverse('login')}?next={url}"
    assert response.url == expected_url


def test_view_edge_cases_no_reported_posts(client: Client, post: Post) -> None:
    PostReport.objects.all().update(verified=True)
    url = reverse("moderator-dashboard")
    response = client.get(url)
    assert response.context is None


def test_view_edge_cases_all_verified_reported_posts(client: Client, post: Post, user: User) -> None:
    url = reverse("moderator-dashboard")
    PostReport.objects.create(post=post, verified=True, report_person=user)
    response = client.get(url)
    assert response.context is None
