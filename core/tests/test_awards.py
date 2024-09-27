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
def test_post_award_level_1() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password=password)
    user.username = "testuser"
    user.community = community
    user.save()
    post = Post.objects.create(author=user, title="Test post", community=community)
    award = PostAward.objects.create(post=post, user=user, choice=PostAward.REWARD_CHOICES[0][0])

    assert award.post == post
    assert award.user == user
    assert post.post_awards.count() == 1
    assert user.awards.count() == 1
    assert award.gold == 15


@pytest.mark.django_db()
def test_post_award_level_2() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password=password)
    user.username = "testuser"
    user.community = community
    user.save()
    post = Post.objects.create(author=user, title="Test post", community=community)
    award = PostAward.objects.create(post=post, user=user, choice=PostAward.REWARD_CHOICES[5][0])

    assert award.post == post
    assert award.user == user
    assert post.post_awards.count() == 1
    assert user.awards.count() == 1
    assert award.gold == 25


@pytest.mark.django_db()
def test_post_award_level_3() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password=password)
    user.username = "testuser"
    user.community = community
    user.save()
    post = Post.objects.create(author=user, title="Test post", community=community)
    award = PostAward.objects.create(post=post, user=user, choice=PostAward.REWARD_CHOICES[10][0])

    assert award.post == post
    assert award.user == user
    assert post.post_awards.count() == 1
    assert user.awards.count() == 1
    assert award.gold == 50


@pytest.mark.django_db()
def test_post_award_all_choices() -> None:
    community = Community.objects.create(name="Test community")
    password = fake.password()
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password=password)
    user.username = "testuser"
    user.community = community
    user.save()
    post = Post.objects.create(author=user, title="Test post", community=community)
    choices = [PostAward.REWARD_CHOICES[0][0], PostAward.REWARD_CHOICES[5][0], PostAward.REWARD_CHOICES[10][0]]
    for choice in choices:
        award = PostAward.objects.create(post=post, user=user, choice=choice)
        assert award.post == post
        assert award.user == user
        assert post.post_awards.count() == 1
        assert user.awards.count() == 1
        if choice == PostAward.REWARD_CHOICES[0][0]:
            assert award.gold == 15
        elif choice == PostAward.REWARD_CHOICES[5][0]:
            assert award.gold == 25
        elif choice == PostAward.REWARD_CHOICES[10][0]:
            assert award.gold == 50
        # usuń nagrodę, aby móc utworzyć następną
        award.delete()


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

    award2 = PostAward.objects.create(post=post, user=user2, choice=PostAward.REWARD_CHOICES[6][0])
    award1 = PostAward.objects.create(post=post, user=user1, choice=PostAward.REWARD_CHOICES[1][0])

    award3 = PostAward.objects.create(post=post, user=user3, choice=PostAward.REWARD_CHOICES[11][0])

    post = Post.objects.get(author=user1, title="Test post", community=community)

    assert post.post_awards.count() == 3
    assert user1.awards.count() == 1
    assert user2.awards.count() == 1
    assert user3.awards.count() == 1
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
    PostAward.objects.create(post=post, user=user2, anonymous=True)
    awards = post.get_post_awards()
    assert len(awards) == 1
    assert awards[0].anonymous_nickname == "Anonymous"
