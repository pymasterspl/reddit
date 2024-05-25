import pytest
from django.contrib.auth import get_user_model

from core.models import Community, Post, PostVote, Tag

User = get_user_model()


@pytest.mark.django_db()
def test_post_score_initial(post: Post) -> None:
    assert post.score == 0


@pytest.mark.django_db()
def test_post_score_upvote(post: Post, user: User) -> None:
    post.vote(user=user, choice=PostVote.UPVOTE)
    post.refresh_from_db()
    assert post.score == 1


@pytest.mark.django_db()
def test_post_score_downvote(post: Post, user: User) -> None:
    post.vote(user=user, choice=PostVote.DOWNVOTE)
    post.refresh_from_db()
    assert post.score == -1


@pytest.mark.django_db()
def test_post_score_multiple_votes(post: Post, user: User, another_user: User) -> None:
    post.vote(user=user, choice=PostVote.UPVOTE)
    post.refresh_from_db()
    assert post.score == 1

    post.vote(user=another_user, choice=PostVote.UPVOTE)
    post.refresh_from_db()
    assert post.score == 2

    post.vote(user=another_user, choice=PostVote.DOWNVOTE)
    post.refresh_from_db()
    assert post.score == 0


@pytest.mark.django_db()
def test_post_score_mixed_votes(post: Post, user: User, another_user: User) -> None:
    post.vote(user=user, choice=PostVote.UPVOTE)
    post.vote(user=another_user, choice=PostVote.DOWNVOTE)

    post.refresh_from_db()
    assert post.score == 0


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

    assert tags.count() == 2
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

    assert tags.count() == 1
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

    assert tags.count() == 3
    assert tags.count() == 3
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

    assert tags.count() == 1
    assert "tag3" in tag_names
    assert "tag1" not in tag_names
    assert "tag2" not in tag_names
