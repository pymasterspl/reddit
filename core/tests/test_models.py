import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from core.models import Community, CommunityMember, Post, PostVote, SavedPost, Tag

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


@pytest.mark.django_db()
def test_create_community_user(user: User, community: Community) -> None:
    community_user: CommunityMember = CommunityMember.objects.create(
        user=user,
        community=community,
        role=CommunityMember.ADMIN,
    )
    community_user.refresh_from_db()

    assert community.members.filter(pk=user.pk).exists()
    assert community_user.community == community
    assert community_user.role == CommunityMember.ADMIN


@pytest.mark.django_db()
def test_default_role(user: User, community: Community) -> None:
    community_user: CommunityMember = CommunityMember.objects.create(
        user=user,
        community=community,
    )

    assert community_user.role == CommunityMember.MEMBER


@pytest.mark.django_db()
def test_unique_community_user(user: User, community: Community) -> None:
    CommunityMember.objects.create(
        user=user,
        community=community,
        role=CommunityMember.MODERATOR,
    )

    with pytest.raises(IntegrityError):
        CommunityMember.objects.create(
            user=user,
            community=community,
            role=CommunityMember.MEMBER,
        )


@pytest.mark.django_db()
def test_save_post(user: User, post: Post) -> None:
    assert SavedPost.objects.filter(user=user).count() == 0
    saved_post = post.save_post(user=user)
    assert SavedPost.objects.filter(user=user, post=post).exists()
    assert saved_post.user == user
    assert saved_post.post == post
    assert SavedPost.objects.filter(user=user).count() == 1


@pytest.mark.django_db()
def test_remove_saved_post(user: User, post: Post) -> None:
    post.save_post(user=user)
    assert SavedPost.objects.filter(user=user).count() == 1
    post.save_post(user=user)
    assert SavedPost.objects.filter(user=user).count() == 1
    post.remove_saved_post(user=user)
    assert not SavedPost.objects.filter(user=user, post=post).exists()


@pytest.mark.django_db()
def test_get_saved_posts(user: User, post: Post) -> None:
    post.save_post(user=user)
    saved_posts = user.get_saved_posts()
    assert saved_posts.count() == 1
    assert saved_posts.first().post == post
    post.remove_saved_post(user=user)
    assert not saved_posts.exists()
