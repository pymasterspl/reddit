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
    ("up_votes", "down_votes", "expected_post_karma", "expected_comment_karma"),
    [
        (10, 2, 8, 0),  # for post
        (2, 10, -8, 0),  # for post
        (5, 1, 0, 4),  # for comment
    ],
)
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_post_and_comment(
    user: User, community: Community, up_votes: int, down_votes: int, expected_post_karma: int, expected_comment_karma: int
) -> None:

    post = Post.objects.create(
        author=user,
        up_votes=up_votes,
        down_votes=down_votes,
        community=community,
        parent=None,
        created_at=timezone.now() - timedelta(days=100),
    )


    comment = Post.objects.create(
        author=user,
        up_votes=up_votes,
        down_votes=down_votes,
        community=community,
        parent=post,
        created_at=timezone.now() - timedelta(days=50),
    )


    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()


    if expected_post_karma != 0:
        assert profile.post_karma == expected_post_karma
    if expected_comment_karma != 0:
        assert profile.comment_karma == expected_comment_karma


@pytest.mark.django_db()
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_two_posts_within_year(user: User, community: Community) -> None:

    Post.objects.create(author=user, up_votes=10, down_votes=2, community=community, parent=None)
    Post.objects.create(author=user, up_votes=5, down_votes=0, community=community, parent=None)

    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()

    assert profile.post_karma == 13
    assert profile.comment_karma == 0


@pytest.mark.django_db()
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_one_post_one_comment(user: User, community: Community) -> None:
    post = Post.objects.create(author=user, up_votes=10, down_votes=2, community=community, parent=None)
    comment = Post.objects.create(author=user, up_votes=3, down_votes=1, community=community, parent=post)

    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()

    assert profile.post_karma == 8
    assert profile.comment_karma == 2


@pytest.mark.django_db()
@freeze_time(FIXED_DATETIME)
def test_calculate_karma_score_two_posts_one_comment_one_expires(user: User, community: Community) -> None:
    post1 = Post.objects.create(author=user, up_votes=10, down_votes=2, community=community, parent=None)
    Post.objects.filter(id=post1.id).update(created_at=timezone.now() - timedelta(days=100))

    post2 = Post.objects.create(author=user, up_votes=5, down_votes=0, community=community, parent=None)
    Post.objects.filter(id=post2.id).update(created_at=timezone.now() - timedelta(days=500))

    comment = Post.objects.create(author=user, up_votes=3, down_votes=1, community=community, parent=post1)

    call_command("update_karma_scores")

    profile = Profile.objects.filter(user_id=user.id).get()

    assert profile.post_karma == 8  # post1 is within the year, post2 is not
    assert profile.comment_karma == 2  # comment is within the year

    # Now simulate the expiration of post1 and its comment
    Post.objects.filter(id=post1.id).update(created_at=timezone.now() - timedelta(days=500))
    Post.objects.filter(id=comment.id).update(created_at=timezone.now() - timedelta(days=500))

    call_command("update_karma_scores")
    profile.refresh_from_db()

    assert profile.post_karma == 0  # both posts are now older than a year
    assert profile.comment_karma == 0  # comment is now older than a year