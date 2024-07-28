import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Post, Community, CommunityMember

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email='user@example.com', nickname='user', password='password')


@pytest.fixture
def user_without_post():
    return User.objects.create_user(email='user2@example.com', nickname='user_without_task', password='password')


@pytest.fixture
def moderator():
    return User.objects.create_user(email='moderator@example.com', nickname='moderator', password='password')


@pytest.fixture
def admin():
    return User.objects.create_user(email='admin@example.com', nickname='admin', password='password')


@pytest.fixture
def community(user):
    return Community.objects.create(name='Test Community', author=user)


@pytest.fixture
def post(user, community):
    return Post.objects.create(author=user, community=community, title='Test Post', content='Content')


@pytest.fixture
def community_member_moderator(moderator, community):
    return CommunityMember.objects.create(user=moderator, community=community, role=CommunityMember.MODERATOR)


@pytest.fixture
def community_member_admin(admin, community):
    member = CommunityMember.objects.create(user=admin, community=community, role=CommunityMember.ADMIN)
    print(f"Admin Community Member: {member}")
    return member


@pytest.mark.django_db
def test_user_can_edit_own_post(user, post):
    assert user.has_permission(post_id=post.id, permission_name='edit') is True


@pytest.mark.django_db
def test_user_cannot_edit_others_post(post, user_without_post):
    assert user_without_post.has_permission(post_id=post.id, permission_name='edit') is False


@pytest.mark.django_db
def test_moderator_can_edit_post(moderator, post, community_member_moderator):
    assert moderator.has_permission(post_id=post.id, permission_name='edit') is True


@pytest.mark.django_db
def test_admin_can_edit_post(admin, post, community_member_admin):
    assert admin.has_permission(post_id=post.id, permission_name='edit') is True


@pytest.mark.django_db
def test_user_without_permission(user, post):
    assert user.has_permission(post_id=post.id, permission_name='nonexistent_permission') is False
