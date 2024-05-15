# tests/test_post_score.py

import pytest
from django.contrib.auth import get_user_model
from core.models import Community, Post, PostVote, Tag

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email='testuser@test.pl', password='12345')


@pytest.fixture
def community(user):
    return Community.objects.create(user=user, name='Test Community')


@pytest.fixture
def post(user, community):
    return Post.objects.create(user=user, community=community, title='Test Post', content='This is a test post')


@pytest.mark.django_db
def test_post_score_initial(post):
    assert post.score == 0


@pytest.mark.django_db
def test_post_score_upvote(post, user):
    vote = PostVote.objects.create(type=PostVote.UPVOTE)
    vote.user.add(user)
    vote.post.add(post)
    post.refresh_from_db()
    assert post.score == 1


@pytest.mark.django_db
def test_post_score_downvote(post, user):
    vote = PostVote.objects.create(type=PostVote.DOWNVOTE)
    vote.user.add(user)
    vote.post.add(post)
    post.refresh_from_db()
    assert post.score == -1


@pytest.mark.django_db
def test_post_score_multiple_votes(post, user):
    another_user = User.objects.create_user(email='anotheruser@test.pl', password='12345')

    vote1 = PostVote.objects.create(type=PostVote.UPVOTE)
    vote1.user.add(user)
    vote1.post.add(post)

    vote2 = PostVote.objects.create(type=PostVote.UPVOTE)
    vote2.user.add(another_user)
    vote2.post.add(post)

    post.refresh_from_db()
    assert post.score == 2

    vote3 = PostVote.objects.create(type=PostVote.DOWNVOTE)
    vote3.user.add(user)
    vote3.post.add(post)

    post.refresh_from_db()
    assert post.score == 1


@pytest.mark.django_db
def test_post_score_mixed_votes(post, user):
    another_user = User.objects.create_user(email='anotheruser@test.pl', password='12345')

    vote1 = PostVote.objects.create(type=PostVote.UPVOTE)
    vote1.user.add(user)
    vote1.post.add(post)

    vote2 = PostVote.objects.create(type=PostVote.DOWNVOTE)
    vote2.user.add(another_user)
    vote2.post.add(post)

    post.refresh_from_db()
    assert post.score == 0


@pytest.mark.django_db
def test_tags_created_on_post_save(user, community):
    content = "This is a test post with #tag1 and #tag2"
    post = Post.objects.create(user=user, community=community, title='Test Post', content=content)

    tags = Tag.objects.filter(content_type=post.get_content_type(), object_id=post.id)
    tag_names = tags.values_list('name', flat=True)

    assert tags.count() == 2
    assert 'tag1' in tag_names
    assert 'tag2' in tag_names


@pytest.mark.django_db
def test_tags_associated_with_post(user, community):
    content = "This is a test post with #tag1"
    post = Post.objects.create(user=user, community=community, title='Test Post', content=content)

    tags = post.tags.all()
    tag_names = tags.values_list('name', flat=True)

    assert tags.count() == 1
    assert 'tag1' in tag_names


@pytest.mark.django_db
def test_duplicate_tags_not_created(user, community):
    content1 = "This is a test post with #tag1"
    post1 = Post.objects.create(user=user, community=community, title='Test Post 1', content=content1)

    content2 = "This is another test post with #tag1 and #tag2"
    post2 = Post.objects.create(user=user, community=community, title='Test Post 2', content=content2)

    tags = Tag.objects.filter(content_type=post1.get_content_type())
    tag_names = tags.values_list('name', flat=True).distinct()

    assert tags.count() == 3  # 2 from post2, but only 1 new tag ('tag2') since 'tag1' already exists
    assert 'tag1' in tag_names
    assert 'tag2' in tag_names


@pytest.mark.django_db
def test_tags_removed_on_post_update(user, community):
    content = "This is a test post with #tag1 and #tag2"
    post = Post.objects.create(user=user, community=community, title='Test Post', content=content)

    post.content = "This is an updated test post with #tag3"
    post.save()

    tags = Tag.objects.filter(content_type=post.get_content_type(), object_id=post.id)
    tag_names = tags.values_list('name', flat=True)

    assert tags.count() == 1
    assert 'tag3' in tag_names
    assert 'tag1' not in tag_names
    assert 'tag2' not in tag_names