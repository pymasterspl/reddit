from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from freezegun import freeze_time

from core.models import Community, Post
from users.models import Profile

User = get_user_model()

FIXED_DATETIME = "2023-01-01 12:00:00"


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("up_votes", "down_votes", "expected_karma"),
    [
        (10, 2, 8),
        (2, 10, -8),
    ],
)
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_one_post(
    user: User, community: Community, up_votes: int, down_votes: int, expected_karma: int
) -> None:
    Post.objects.create(
        author=user,
        up_votes=up_votes,
        down_votes=down_votes,
        community=community,
        created_at=timezone.now() - timedelta(days=100),
    )

    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()

    assert profile.karma_score == expected_karma


@pytest.mark.django_db()
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_two_posts_within_year(user: User, community: Community) -> None:
    Post.objects.create(author=user, up_votes=10, down_votes=2, community=community)

    Post.objects.create(author=user, up_votes=5, down_votes=0, community=community)

    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()

    assert profile.karma_score == 13


@pytest.mark.django_db()
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_two_posts_one_older_than_year(user: User, community: Community) -> None:
    post1 = Post.objects.create(author=user, up_votes=10, down_votes=2, community=community)
    Post.objects.filter(id=post1.id).update(created_at=timezone.now() - timedelta(days=100))

    post2 = Post.objects.create(author=user, up_votes=5, down_votes=0, community=community)
    Post.objects.filter(id=post2.id).update(created_at=timezone.now() - timedelta(days=500))

    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()

    assert profile.karma_score == 8


@pytest.mark.django_db()
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_one_post_expires(user: User, community: Community) -> None:
    post = Post.objects.create(author=user, up_votes=10, down_votes=2, community=community)

    call_command("update_karma_scores")
    profile = Profile.objects.filter(user_id=user.id).get()
    assert profile.karma_score == 8

    Post.objects.filter(id=post.id).update(created_at=timezone.now() - timedelta(days=500))
    call_command("update_karma_scores")
    profile.refresh_from_db()
    assert profile.karma_score == 0
