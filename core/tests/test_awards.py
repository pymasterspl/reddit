# Standard library imports
import pytest

# Django and third-party imports
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from faker import Faker

# Local application imports
from core.models import PostAward

User = get_user_model()
fake = Faker()


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("choice", "expected_gold"),
    [
        (PostAward.get_reward_choices()[0][0], 15),
        (PostAward.get_reward_choices()[5][0], 25),
        (PostAward.get_reward_choices()[10][0], 50),
    ],
)
def test_post_award_level(choice: str, expected_gold: int, users, post) -> None:
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
def test_post_award_multiple_users(users, post) -> None:
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
def test_post_award_anonymous(users, post) -> None:
    post.author = users[0]
    PostAward.objects.create(
        receiver=post.author, post=post, giver=users[1], anonymous=True, choice=PostAward.get_reward_choices()[0][0]
    )
    PostAward.objects.create(
        receiver=post.author, post=post, giver=users[0], anonymous=False, choice=PostAward.get_reward_choices()[0][0]
    )
    awards = post.get_post_awards()
    assert len(awards) == 2
    assert awards[0]["giver_anonim"] == "Anonymous"
    assert awards[1]["giver_anonim"] == "test_user_1"


@pytest.mark.django_db()
def test_post_award_duplicate_prevention(users, post, user) -> None:
    post.author = user
    PostAward.objects.create(
        receiver=post.author, post=post, giver=users[1], choice=PostAward.get_reward_choices()[0][0]
    )

    with pytest.raises(
        IntegrityError, match="UNIQUE constraint failed: core_postaward.post_id, core_postaward.giver_id"
    ):
        PostAward.objects.create(
            receiver=post.author, post=post, giver=users[1], choice=PostAward.get_reward_choices()[0][0]
        )


@pytest.mark.django_db()
def test_cannot_give_award_to_own_post(client, user, post):
    client.force_login(user)  # log in user
    award_url = reverse("post-award", kwargs={"pk": post.pk})
    response = client.post(award_url, {"choice": "1"})  # try to add award to your own post

    assert response.status_code == 302  # check if user is unable to give reward to his own post
    assert PostAward.objects.count() == 0  # check if user is unable to give reward to his own post
