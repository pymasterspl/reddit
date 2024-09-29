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
def test_post_award_level(choice: str, expected_gold: int) -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password=password)
    user2 = User.objects.create_user(email="testuser2@example.com", nickname="testuser2", password=password)
    user.username = "testuser"
    user.community = community
    user.save()
    user2.username = "testuser2"
    user2.community = community
    user2.save()
    post = Post.objects.create(author=user2, title="Test post", community=community)
    award = PostAward.objects.create(post=post, giver=user, choice=choice)
    user2.profile.refresh_from_db()
    post.refresh_from_db()
    award.refresh_from_db()
    

    assert award.post == post
    assert award.giver == user
    assert post.post_awards.count() == 1
    assert user.awards_given.count() == 1
    assert award.gold == expected_gold
    assert post.gold == expected_gold
    assert user2.profile.gold_awards == expected_gold


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("choice", "expected_gold"),
    [
        (PostAward.get_reward_choices()[0][0], 15),
        (PostAward.get_reward_choices()[5][0], 25),
        (PostAward.get_reward_choices()[10][0], 50),
    ],
)
def test_post_award_all_choices(choice: str, expected_gold: int) -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password=password)
    post = Post.objects.create(author=user, title="Test post", community=community)
    award = PostAward.objects.create(post=post, giver=user, choice=choice)
    assert award.post == post
    assert award.giver == user
    assert award.gold == expected_gold
    assert post.post_awards.count() == 1
    assert user.awards_given.count() == 1


@pytest.mark.django_db()
def test_post_award_multiple_users() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user1 = User.objects.create_user(email="testuser1@example.com", nickname="testuser1", password=password)
    user1.username = "testuser1"
    user1.community = community
    user1.save()
    user2 = User.objects.create_user(email="testuser2@example.com", nickname="testuser2", password=password)
    user2.username = "testuser2"
    user2.community = community
    user2.save()
    user3 = User.objects.create_user(email="testuser3@example.com", nickname="testuser3", password=password)
    user3.username = "testuser3"
    user3.community = community
    user3.save()
    post = Post.objects.create(author=user1, title="Test post", community=community)

    award1 = PostAward.objects.create(post=post, giver=user1, choice=PostAward.get_reward_choices()[1][0])
    award2 = PostAward.objects.create(post=post, giver=user2, choice=PostAward.get_reward_choices()[6][0])
    award3 = PostAward.objects.create(post=post, giver=user3, choice=PostAward.get_reward_choices()[11][0])

    post = Post.objects.get(author=user1, title="Test post", community=community)
    user1 = User.objects.get(email="testuser1@example.com", nickname="testuser1")

    assert post.post_awards.count() == 3
    assert user1.awards_given.count() == 1
    assert user2.awards_given.count() == 1
    assert user3.awards_given.count() == 1
    assert award1.gold == 15
    assert award2.gold == 25
    assert award3.gold == 50
    assert post.gold == 15 + 25 + 50
    assert user1.profile.gold_awards == 15 + 25 + 50


@pytest.mark.django_db()
def test_post_award_anonymous() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user1 = User.objects.create_user(email="test@example.com", password=password, nickname="testuser1")
    user2 = User.objects.create_user(email="test2@example.com", password=password, nickname="testuser2")
    post = Post.objects.create(author=user1, title="Test post", content="Test content", community=community)
    PostAward.objects.create(post=post, giver=user2, anonymous=True)
    PostAward.objects.create(post=post, giver=user1, anonymous=False)
    awards = post.get_post_awards()
    assert len(awards) == 2
    assert awards[0]["giver_anonim"] == "Anonymous"
    assert awards[1]["giver_anonim"] == "testuser1"


@pytest.mark.django_db()
def test_post_award_duplicate_prevention() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="test@example.com", password=password, nickname="testuser")
    post = Post.objects.create(author=user, title="Test post", content="Test content", community=community)

    PostAward.objects.create(post=post, giver=user, choice=PostAward.get_reward_choices()[0][0])

    with pytest.raises(ValueError, match="Already given award"):
        PostAward.objects.create(post=post, giver=user, choice=PostAward.get_reward_choices()[0][0])
