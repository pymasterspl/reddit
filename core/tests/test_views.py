import secrets
import string

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse
from faker import Faker

from core.models import Community, Post, PostReport

pytestmark = pytest.mark.django_db

User = get_user_model()


def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(characters) for _ in range(length))


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


@pytest.fixture()
def admin(client: Client) -> User:
    password = generate_random_password()
    user = User.objects.create_user(
        email="test_admin@example.com", nickname="TestAdmin", password=password, is_superuser=True, is_staff=True
    )

    client.login(email=user.email, password=user.password)
    return user


@pytest.fixture()
def community() -> Community:
    return Community.objects.create(name="Test Community", is_active=True)


@pytest.fixture()
def report_data() -> dict:
    fake = Faker()
    return {
        "report_type": "EU_ILLEGAL_CONTENT",
        "report_details": fake.text(max_nb_chars=100),
    }


@pytest.fixture()
def post_report(post: Post, user: User) -> Post:
    fake = Faker()
    return PostReport.objects.create(
        post=post, report_type="THREATENING_VIOLENCE", report_details=fake.text(max_nb_chars=100), report_person=user
    )


@pytest.fixture()
def admin_action_form_data() -> dict:
    return {"action": "DELETE", "comment": "This post violates the guidelines."}


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
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=report_data)
    assert response.status_code == 302
    assert reverse("home") in response.url
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_report_post_unauthorized(client: Client, post: Post, report_data: dict) -> None:
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=report_data)
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


def test_reported_list_post_by_admin(client: Client, admin: User, post: Post, report_data: dict) -> None:
    client.force_login(admin)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=report_data)
    assert response.status_code == 302
    assert reverse("home") in response.url
    response = client.get(reverse("post-list-reported"))
    assert response.status_code == 200

    reports_count = PostReport.objects.filter(verified=False).count()
    assert reports_count > 0


def test_reported_list_post_by_user(client: Client, user: User, post: Post, report_data: dict) -> None:
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=report_data)
    assert response.status_code == 302
    assert reverse("home") in response.url
    response = client.get(reverse("post-list-reported"))
    assert response.status_code == 302
    assert reverse("home") in response.url


def test_reported_list_post_by_anonymous_user(client: Client) -> None:
    response = client.get(reverse("post-list-reported"))
    assert response.status_code == 302
    assert "/accounts/login/?next=/core/reported-posts/" in response.url


def test_reported_detail_post_by_user(client: Client, user: User, post: Post, report_data: dict) -> None:
    client.force_login(user)
    response = client.post(reverse("post-report", kwargs={"pk": post.pk}), data=report_data)
    assert response.status_code == 302
    assert reverse("home") in response.url
    response = client.get(reverse("reported-post", kwargs={"pk": 1}))
    assert response.status_code == 403


def test_reported_detail_post_by_anonymous_user(client: Client, post_report: PostReport) -> None:
    response = client.get(reverse("post-report", kwargs={"pk": post_report.pk}))
    assert response.status_code == 302
    assert f"/users/login/?next=/core/post/report/{post_report.pk}/" in response.url


def test_reported_detail_post_by_admin(
    client: Client, admin: User, post: Post, post_report: PostReport, admin_action_form_data: dict
) -> None:
    client.force_login(admin)
    response = client.post(reverse("reported-post", kwargs={"pk": post_report.pk}), data=admin_action_form_data)
    assert response.status_code == 302

    with pytest.raises(Post.DoesNotExist):
        post.refresh_from_db()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Post Deleted"
    assert mail.outbox[0].to == [post.author.email]


def test_add_nested_comment_valid(client: Client, another_user: User, post: Post, comment: Post) -> None:
    data = {
        "parent_id": comment.pk,
        "content": "This is a test nested comment content.",
    }
    client.force_login(another_user)
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
    assert new_comment.author == another_user
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


def test_add_deeply_nested_comment_valid(client: Client, another_user: User, post: Post) -> None:
    client.force_login(another_user)
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
