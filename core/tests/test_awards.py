# Standard library imports
import pytest
from django.contrib import messages

# Django imports
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse
from faker import Faker

# Local application imports
from core.models import Post, PostAward

User = get_user_model()
fake = Faker()


@pytest.mark.django_db()
def test_post_award_anonymous(users: list[User], post: Post) -> None:
    post.author = users[0]
    PostAward.objects.create(
        receiver=post.author, post=post, giver=users[1], anonymous=True, choice=PostAward.get_reward_choices()[0][0]
    )
    PostAward.objects.create(
        receiver=post.author, post=post, giver=users[0], anonymous=False, choice=PostAward.get_reward_choices()[0][0]
    )
    users[0].profile.refresh_from_db()
    awards = post.get_post_awards()
    assert len(awards) == 2
    assert post.author.profile.gold_awards == 30
    assert awards[0]["giver_anonymous"] == "Anonymous"
    assert awards[1]["giver_anonymous"] == "test_user_1"


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("choice", "expected_gold"),
    [
        (PostAward.get_reward_choices()[0][0], 15),
        (PostAward.get_reward_choices()[5][0], 25),
        (PostAward.get_reward_choices()[10][0], 50),
    ],
)
def test_post_award_level(choice: str, expected_gold: int, users: list[User], post: Post) -> None:
    post.author = users[0]
    award = PostAward.objects.create(receiver=post.author, post=post, giver=users[1], choice=choice)
    users[1].profile.refresh_from_db()
    post.refresh_from_db()
    award.refresh_from_db()
    users[0].profile.refresh_from_db()

    assert award.post == post
    assert award.giver == users[1]
    assert post.post_awards.count() == 1
    assert users[1].awards_given.count() == 1
    assert award.gold == expected_gold
    assert post.gold == expected_gold
    assert users[0].profile.gold_awards == expected_gold


@pytest.mark.django_db()
def test_post_award_multiple_users(users: list[User], post: Post) -> None:
    post.author = users[0]
    award1 = PostAward.objects.create(
        receiver=post.author, post=post, giver=users[0], choice=PostAward.get_reward_choices()[1][0]
    )
    award2 = PostAward.objects.create(
        receiver=post.author, post=post, giver=users[1], choice=PostAward.get_reward_choices()[6][0]
    )
    award3 = PostAward.objects.create(
        receiver=post.author, post=post, giver=users[2], choice=PostAward.get_reward_choices()[11][0]
    )
    post.refresh_from_db()
    users[0].profile.refresh_from_db()

    assert post.post_awards.count() == 3
    assert users[0].awards_given.count() == 1
    assert users[1].awards_given.count() == 1
    assert users[2].awards_given.count() == 1
    assert award1.gold == 15
    assert award2.gold == 25
    assert award3.gold == 50
    assert post.gold == 15 + 25 + 50
    assert users[0].profile.gold_awards == 15 + 25 + 50


@pytest.mark.django_db()
def test_post_award_duplicate_prevention(users: list[User], post: Post, user: User) -> None:
    post.author = user
    award = PostAward.objects.create(
        receiver=post.author, post=post, giver=users[1], choice=PostAward.get_reward_choices()[0][0]
    )

    assert PostAward.objects.filter(id=award.id).exists()

    with pytest.raises(
        IntegrityError, match="UNIQUE constraint failed: core_postaward.post_id, core_postaward.giver_id"
    ):
        PostAward.objects.create(
            receiver=post.author, post=post, giver=users[1], choice=PostAward.get_reward_choices()[0][0]
        )


@pytest.mark.django_db()
def test_cannot_give_award_to_own_post(client: Client, user: User, post: Post) -> None:
    client.force_login(user)  # log in user
    award_url = reverse("post-award", kwargs={"pk": post.pk})
    response = client.post(award_url, {"choice": "1"})  # try to add award to your own post
    msg_storage = list(messages.get_messages(response.wsgi_request))

    assert response.status_code == 302  # check if user is unable to give reward to his own post
    assert PostAward.objects.count() == 0  # check if user is unable to give reward to his own post
    assert msg_storage[0].message == "You cannot give an award to your own post"


@pytest.mark.django_db()
def test_award_comment(user: User, post: Post) -> None:
    award = PostAward.objects.create(
        receiver=post.author, post=post, giver=user, choice=PostAward.get_reward_choices()[0][0], comment="Test comment"
    )
    assert award.comment == "Test comment"
