import io
from pathlib import Path

import pytest
from django.conf import Settings, settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from PIL import Image

from core.models import Community, CommunityMember, Post

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
    return user


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


@pytest.fixture()
def user_with_avatar(client: Client, create_avatar: SimpleUploadedFile, another_user: User) -> User:
    another_user.avatar = create_avatar
    another_user.save()
    client.login(email=another_user.email, password=another_user.password)
    return another_user


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
def default_avatar_url(settings: Settings) -> None:
    return settings.DEFAULT_AVATAR_URL


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
