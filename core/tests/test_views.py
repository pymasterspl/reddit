import io
from pathlib import Path

import pytest
from django.conf import Settings, settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse, reverse_lazy
from faker import Faker
from PIL import Image

from core.models import BAN, DELETE, DISMISS_REPORT, WARN, Community, CommunityMember, Post, PostReport

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
    user.avatar = create_avatar
    user.save()
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
def post_report(post: Post, user: User) -> Post:
    fake = Faker()
    return PostReport.objects.create(
        post=post, report_type="THREATENING_VIOLENCE", report_details=fake.text(max_nb_chars=100), report_person=user
    )


@pytest.fixture()
def admin_action_form_data() -> dict:
    return {"action": "20_DELETE", "comment": "This post violates the guidelines."}


@pytest.fixture()
def default_avatar_url(settings: Settings) -> None:
    return settings.DEFAULT_AVATAR_URL


@pytest.fixture()
def restricted_community(user: User) -> Community:
    return Community.objects.create(name="Restricted Community", is_active=True, author=user)


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


def test_reported_list_post_by_admin(client: Client, admin: User, post: Post, report_data: dict) -> None:
    data = report_data()
    client.force_login(admin)
    client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    response = client.get(reverse("post-list-reported"))
    assert response.status_code == 200
    reports_count = PostReport.objects.filter(verified=False).count()
    assert reports_count == 1


def test_reported_list_post_by_user(client: Client, user: User, post: Post, report_data: dict) -> None:
    data = report_data()
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    assert response.status_code == 302
    response = client.get(reverse("post-list-reported"))
    assert response.status_code == 302
    assert response.url == reverse("home")

    messages = list(get_messages(response.wsgi_request))
    assert any("You do not have permission to view this page." in str(message) for message in messages)


def test_reported_list_post_by_anonymous_user(client: Client) -> None:
    response = client.get(reverse("post-list-reported"))
    assert response.status_code == 302
    assert str(reverse_lazy("post-list-reported")) in response.url


def test_reported_detail_post_by_user(client: Client, user: User, post: Post, report_data: dict) -> None:
    data = report_data()
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=data)
    client.force_login(user)
    response = client.get(reverse("reported-post", kwargs={"pk": post.pk}))
    assert response.status_code == 403
    assert "<h1>403 Forbidden</h1>" in response.content.decode()


def test_reported_detail_post_by_anonymous_user(client: Client, post_report: PostReport) -> None:
    response = client.get(reverse("post-report", kwargs={"pk": post_report.pk}))
    assert response.status_code == 302
    assert f"{settings.LOGIN_URL}?next={reverse('post-report', kwargs={'pk': post_report.pk})}" in response.url


def test_reported_detail_post_by_admin(
    client: Client, admin: User, user: User, admin_action_form_data: dict, community: Community
) -> None:
    fake = Faker()
    for action in [DELETE, WARN, DISMISS_REPORT, BAN]:
        client.force_login(admin)
        post = Post.objects.create(
            author=user,
            community=community,
            title="Test Post",
            content="This is a test post",
        )
        post_report = PostReport.objects.create(
            post=post,
            report_type="THREATENING_VIOLENCE",
            report_details=fake.text(max_nb_chars=100),
            report_person=user,
        )
        admin_action_form_data["action"] = action
        mail.outbox = []

        response = client.post(
            reverse_lazy("reported-post", kwargs={"pk": post_report.pk}),
            data=admin_action_form_data,
            follow_redirects=True,
        )

        assert response.status_code == 302
        if action in [DELETE, WARN, BAN]:
            assert len(mail.outbox) == 1, f"Expected 1 email for action '{action}', but got {len(mail.outbox)}"
            email = mail.outbox[0]
            if action == BAN:
                assert email.subject == "Account Banned"
                assert email.to == [post_report.post.author.email]
                client.logout()
                login_data = {"email": user.email, "password": user.plain_password}
                response = client.post(reverse("login"), data=login_data)
                assert response.status_code == 200
                assert not response.wsgi_request.user.is_authenticated
            elif action == DELETE:
                post.refresh_from_db()
                assert not post.is_active, "Post should be marked as inactive"
                if post.is_active:
                    assert len(mail.outbox) == 1, "Expected 1 email, but found none"
                    email = mail.outbox[0]
                    assert email.subject == "Post Deleted"
                    assert email.to == [post_report.post.author.email]
            elif action == WARN:
                assert email.subject in ["Warning Issued", "Post Deleted"]
                assert email.to == [post_report.post.author.email]
        else:
            assert len(mail.outbox) == 0, f"Expected no email for action '{action}', but got {len(mail.outbox)}"


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
    assert post.author.avatar.url == user_with_avatar.avatar_url


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
    assert post.author.avatar_url == default_avatar_url


def test_restricted_community_access(client: Client, restricted_community: Community, user: User) -> None:
    client.force_login(user)
    response = client.get(reverse("community-detail", kwargs={"slug": restricted_community.slug}))
    assert response.status_code == 200


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
