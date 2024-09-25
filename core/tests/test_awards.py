import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from core.models import Post, User, PostAward, Community

User = get_user_model()


@pytest.mark.django_db()
def test_post_award_level_1():
    community = Community.objects.create(name="Test community")
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password="password")
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
def test_post_award_level_2():
    community = Community.objects.create(name="Test community")
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password="password")
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
def test_post_award_level_3():
    community = Community.objects.create(name="Test community")
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password="password")
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
def test_post_award_all_choices():
    community = Community.objects.create(name="Test community")
    user = User.objects.create_user(email="testuser@example.com", nickname="testuser", password="password")
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
def test_post_award_multiple_users():
    community = Community.objects.create(name="Test community")
    user1 = User.objects.create_user(email="testuser1@example.com", nickname="testuser1", password="password")
    user1.username = "testuser1"
    user1.community = community
    user1.save()
    user2 = User.objects.create_user(email="testuser2@example.com", nickname="testuser2", password="password")
    user2.username = "testuser2"
    user2.community = community
    user2.save()
    user3 = User.objects.create_user(email="testuser3@example.com", nickname="testuser3", password="password")
    user3.username = "testuser3"
    user3.community = community
    user3.save()
    post = Post.objects.create(author=user1, title="Test post", community=community)

    award1 = PostAward.objects.create(post=post, user=user1, choice=PostAward.REWARD_CHOICES[1][0])
    award2 = PostAward.objects.create(post=post, user=user2, choice=PostAward.REWARD_CHOICES[6][0])
    award3 = PostAward.objects.create(post=post, user=user3, choice=PostAward.REWARD_CHOICES[11][0])

    assert post.post_awards.count() == 3
    assert user1.awards.count() == 1
    assert user2.awards.count() == 1
    assert user3.awards.count() == 1
    assert award1.gold == 15
    assert award2.gold == 25
    assert award3.gold == 50
    post = Post.objects.get(author=user1, title="Test post", community=community)
    assert post.gold == 15 + 25 + 50


@pytest.mark.django_db()
def test_post_award_anonymous():
    community = Community.objects.create(name="Test community")
    post = Post.objects.create(title="Test post", content="Test content", community=community)
    user = User.objects.create_user(email="test@example.com", password="testpassword", nickname="testuser")
    post_award = PostAward.objects.create(post=post, user=user, anonymous=True)
    awards = post.get_post_awards()
    assert len(awards) == 1
    assert awards[0].user.nickname == "Anonymous"
