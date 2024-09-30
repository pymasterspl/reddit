# Standard library imports
import pytest

# Django and third-party imports
from django.contrib.auth import get_user_model
from faker import Faker

# Local application imports
from core.models import Community, Post, PostAward

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
    award = PostAward.objects.create(post=post, giver=users[1], choice=choice)
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
    award1 = PostAward.objects.create(post=post, giver=users[0], choice=PostAward.get_reward_choices()[1][0])
    award2 = PostAward.objects.create(post=post, giver=users[1], choice=PostAward.get_reward_choices()[6][0])
    award3 = PostAward.objects.create(post=post, giver=users[2], choice=PostAward.get_reward_choices()[11][0])
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
    PostAward.objects.create(post=post, giver=users[1], anonymous=True, choice=PostAward.get_reward_choices()[0][0])
    PostAward.objects.create(post=post, giver=users[0], anonymous=False, choice=PostAward.get_reward_choices()[0][0])
    awards = post.get_post_awards()
    assert len(awards) == 2
    assert awards[0]["giver_anonim"] == "Anonymous"
    assert awards[1]["giver_anonim"] == "test_user_1"

    
@pytest.mark.django_db()
def test_post_award_duplicate_prevention(user, post) -> None:

    PostAward.objects.create(post=post, giver=user, choice=PostAward.get_reward_choices()[0][0])

    with pytest.raises(ValueError, match="Already given award"):
        PostAward.objects.create(post=post, giver=user, choice=PostAward.get_reward_choices()[0][0])
