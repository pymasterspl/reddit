import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.models import PostVote

User = get_user_model()


@pytest.mark.django_db()
def test_upvoted_post(client: Client, user: User, upvote_post: PostVote) -> None:
    url = reverse("user_upvoted")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_post.post in response.context["posts"]
    assert len(response.context["posts"]) == 1


@pytest.mark.django_db()
def test_upvoted_comment(client: Client, user: User, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_comment.post in response.context["posts"]
    assert len(response.context["posts"]) == 1


@pytest.mark.django_db()
def test_upvoted_filter_post(client: Client, user: User, upvote_post: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter=post"
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_post.post in response.context["posts"]
    assert len(response.context["posts"]) == 1


@pytest.mark.django_db()
def test_upvoted_filter_post_empty(client: Client, user: User, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter=post"
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_comment.post not in response.context["posts"]
    assert len(response.context["posts"]) == 0


@pytest.mark.django_db()
def test_upvoted_filter_comment(client: Client, user: User, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter=comment"
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_comment.post in response.context["posts"]
    assert len(response.context["posts"]) == 1


@pytest.mark.django_db()
def test_upvoted_filter_comment_empty(client: Client, user: User, upvote_post: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter=comment"
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_post.post not in response.context["posts"]
    assert len(response.context["posts"]) == 0


@pytest.mark.django_db()
def test_upvoted_filter_all_post(client: Client, user: User, upvote_post: PostVote, upvote_comment: PostVote) -> None:
    url = reverse("user_upvoted") + "?filter="
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert upvote_post.post in response.context["posts"]
    assert upvote_comment.post in response.context["posts"]
    assert len(response.context["posts"]) == 2


@pytest.mark.django_db()
def test_downvoted_post(client: Client, user: User, downvote_post: PostVote) -> None:
    url = reverse("user_downvoted")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert downvote_post.post in response.context["posts"]
    assert len(response.context["posts"]) == 1


@pytest.mark.django_db()
def test_downvoted_comment(client: Client, user: User, downvote_comment: PostVote) -> None:
    url = reverse("user_downvoted")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert downvote_comment.post in response.context["posts"]
    assert len(response.context["posts"]) == 1


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "data",
    [
        {"filter": "post", "type": "downvote_post", "present": True, "count": 1},
        {"filter": "post", "type": "downvote_comment", "present": False, "count": 0},
        {"filter": "comment", "type": "downvote_comment", "present": True, "count": 1},
        {"filter": "comment", "type": "downvote_post", "present": False, "count": 0},
    ],
)
def test_downvoted_filter(client: Client, user: User, request: pytest.FixtureRequest, data: dict) -> None:
    url = reverse("user_downvoted") + f"?filter={data['filter']}"
    client.force_login(user)
    vote = request.getfixturevalue(data["type"])
    response = client.get(url)
    assert response.status_code == 200
    assert (vote.post in response.context["posts"]) == data["present"]
    assert len(response.context["posts"]) == data["count"]


@pytest.mark.django_db()
def test_downvoted_filter_all_post(
    client: Client, user: User, downvote_post: PostVote, downvote_comment: PostVote
) -> None:
    url = reverse("user_downvoted") + "?filter="
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert downvote_post.post in response.context["posts"]
    assert downvote_comment.post in response.context["posts"]
    assert len(response.context["posts"]) == 2
