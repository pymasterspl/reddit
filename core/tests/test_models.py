import secrets
import string
from collections.abc import Generator

import pytest
from django.contrib.auth import get_user_model

from core.models import Community, Post, PostVote, Tag

User = get_user_model()

UPVOTE_SCORE = 1
DOWNVOTE_SCORE = -1
MULTIPLE_VOTES_SCORE = 2
SCORE_3 = 3
MIXED_VOTES_SCORE = 0


def generate_random_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation

    return "".join(secrets.choice(alphabet) for i in range(length))


@pytest.fixture()
def user() -> Generator[User, None, None]:
    return User.objects.create_user(
        email="testuser@test.pl",
        password=generate_random_password(),
    )


@pytest.fixture()
def community(user: User) -> Generator[Community, None, None]:
    return Community.objects.create(user=user, name="Test Community")


@pytest.fixture()
def post(user: User, community: Community) -> Generator[Post, None, None]:
    return Post.objects.create(
        user=user,
        community=community,
        title="Test Post",
        content="This is a test post",
    )


@pytest.mark.django_db()
def test_post_score_initial(post: Post) -> None:
    assert post.score == MIXED_VOTES_SCORE


@pytest.mark.django_db()
def test_post_score_upvote(post: Post, user: User) -> None:
    vote = PostVote.objects.create(type=PostVote.UPVOTE)
    vote.user.add(user)
    vote.post.add(post)
    post.refresh_from_db()
    assert post.score == UPVOTE_SCORE


@pytest.mark.django_db()
def test_post_score_downvote(post: Post, user: User) -> None:
    vote = PostVote.objects.create(type=PostVote.DOWNVOTE)
    vote.user.add(user)
    vote.post.add(post)
    post.refresh_from_db()
    assert post.score == DOWNVOTE_SCORE


@pytest.mark.django_db()
def test_post_score_multiple_votes(post: Post, user: User) -> None:
    another_user = User.objects.create_user(
        email="anotheruser@test.pl",
        password=generate_random_password(),
    )

    vote1 = PostVote.objects.create(type=PostVote.UPVOTE)
    vote1.user.add(user)
    vote1.post.add(post)

    vote2 = PostVote.objects.create(type=PostVote.UPVOTE)
    vote2.user.add(another_user)
    vote2.post.add(post)

    post.refresh_from_db()
    assert post.score == MULTIPLE_VOTES_SCORE

    vote3 = PostVote.objects.create(type=PostVote.DOWNVOTE)
    vote3.user.add(user)
    vote3.post.add(post)

    post.refresh_from_db()
    assert post.score == UPVOTE_SCORE


@pytest.mark.django_db()
def test_post_score_mixed_votes(post: Post, user: User) -> None:
    another_user = User.objects.create_user(
        email="anotheruser@test.pl",
        password=generate_random_password(),
    )

    vote1 = PostVote.objects.create(type=PostVote.UPVOTE)
    vote1.user.add(user)
    vote1.post.add(post)

    vote2 = PostVote.objects.create(type=PostVote.DOWNVOTE)
    vote2.user.add(another_user)
    vote2.post.add(post)

    post.refresh_from_db()
    assert post.score == MIXED_VOTES_SCORE


@pytest.mark.django_db()
def test_tags_created_on_post_save(user: User, community: Community) -> None:
    content = "This is a test post with #tag1 and #tag2"
    post = Post.objects.create(
        user=user,
        community=community,
        title="Test Post",
        content=content,
    )

    tags = Tag.objects.filter(content_type=post.get_content_type(), object_id=post.id)
    tag_names = tags.values_list("name", flat=True)

    assert tags.count() == MULTIPLE_VOTES_SCORE
    assert "tag1" in tag_names
    assert "tag2" in tag_names


@pytest.mark.django_db()
def test_tags_associated_with_post(user: User, community: Community) -> None:
    content = "This is a test post with #tag1"
    post = Post.objects.create(
        user=user,
        community=community,
        title="Test Post",
        content=content,
    )

    tags = post.tags.all()
    tag_names = tags.values_list("name", flat=True)

    assert tags.count() == UPVOTE_SCORE
    assert "tag1" in tag_names


@pytest.mark.django_db()
def test_duplicate_tags_not_created(user: User, community: Community) -> None:
    content1 = "This is a test post with #tag1"
    post1 = Post.objects.create(
        user=user,
        community=community,
        title="Test Post 1",
        content=content1,
    )

    content2 = "This is another test post with #tag1 and #tag2"
    Post.objects.create(
        user=user,
        community=community,
        title="Test Post 2",
        content=content2,
    )

    tags = Tag.objects.filter(content_type=post1.get_content_type())
    tag_names = tags.values_list("name", flat=True).distinct()

    assert tags.count() == SCORE_3
    assert tags.count() == SCORE_3
    assert "tag1" in tag_names
    assert "tag2" in tag_names


@pytest.mark.django_db()
def test_tags_removed_on_post_update(user: User, community: Community) -> None:
    content = "This is a test post with #tag1 and #tag2"
    post = Post.objects.create(
        user=user,
        community=community,
        title="Test Post",
        content=content,
    )

    post.content = "This is an updated test post with #tag3"
    post.save()

    tags = Tag.objects.filter(content_type=post.get_content_type(), object_id=post.id)
    tag_names = tags.values_list("name", flat=True)

    assert tags.count() == UPVOTE_SCORE
    assert "tag3" in tag_names
    assert "tag1" not in tag_names
    assert "tag2" not in tag_names
