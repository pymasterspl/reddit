import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import Post, PostVote

User = get_user_model()


@pytest.mark.django_db()
def test_upvoted_post(client: Client, user: User, post: Post, upvote_post: PostVote) -> None:
    url = reverse("user_upvoted")
    client.force_login(user)
    response = client.get(url)
    post.refresh_from_db()
    upvote_post.refresh_from_db()
    assert response.status_code == 200
    assert upvote_post.post == post
    assert upvote_post.choice == PostVote.UPVOTE
    assert post.up_votes == 1


@pytest.mark.django_db()
def test_upvoted_comment(client: Client, user: User, comment: Post, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted")
    client.force_login(user)
    response = client.get(url)
    comment.refresh_from_db()
    upvote_comment.refresh_from_db()
    assert response.status_code == 200
    assert upvote_comment.post == comment
    assert upvote_comment.choice == PostVote.UPVOTE
    assert comment.up_votes == 1


@pytest.mark.django_db()
def test_filter_post(client: Client, user: User, post: Post, upvote_post: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter=post"
    client.force_login(user)
    response = client.get(url)
    post.refresh_from_db()
    upvote_post.refresh_from_db()
    assert response.status_code == 200
    assert post in response.context["posts"]


@pytest.mark.django_db()
def test_filter_comment(client: Client, user: User, comment: Post, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter=comment"
    client.force_login(user)
    response = client.get(url)
    comment.refresh_from_db()
    upvote_comment.refresh_from_db()
    assert response.status_code == 200
    assert comment in response.context["posts"]


@pytest.mark.django_db()
def test_filter_all_post(client: Client, user: User, post: Post, upvote_post: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter="
    client.force_login(user)
    response = client.get(url)
    post.refresh_from_db()
    upvote_post.refresh_from_db()
    assert response.status_code == 200
    assert post in response.context["posts"]


@pytest.mark.django_db()
def test_filter_all_comment(client: Client, user: User, comment: Post, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter="
    client.force_login(user)
    response = client.get(url)
    comment.refresh_from_db()
    upvote_comment.refresh_from_db()
    assert response.status_code == 200
    assert comment in response.context["posts"]
