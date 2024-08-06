import pytest
from django.contrib.auth.hashers import make_password

from core.models import Community, CommunityMember, Post
from users.models import User


@pytest.fixture()
def user() -> User:
    return User.objects.create_user(
        email="user@example.com", nickname="user", password=make_password("password")
    )


@pytest.fixture()
def user_without_post() -> User:
    return User.objects.create_user(
        email="user2@example.com",
        nickname="user_without_task",
        password=make_password("password"),
    )


@pytest.fixture()
def moderator() -> User:
    return User.objects.create_user(
        email="moderator@example.com",
        nickname="moderator",
        password=make_password("password"),
    )


@pytest.fixture()
def admin() -> User:
    return User.objects.create_user(
        email="admin@example.com", nickname="admin", password=make_password("password")
    )


@pytest.fixture()
def community(user: User) -> Community:
    return Community.objects.create(name="Test Community", author=user)


@pytest.fixture()
def post(user: User, community: Community) -> Post:
    return Post.objects.create(
        author=user, community=community, title="Test Post", content="Content"
    )


@pytest.fixture()
def community_member_moderator(
    moderator: User, community: Community
) -> CommunityMember:
    return CommunityMember.objects.create(
        user=moderator, community=community, role=CommunityMember.MODERATOR
    )


@pytest.fixture()
def community_member_admin(admin: User, community: Community) -> CommunityMember:
    return CommunityMember.objects.create(
        user=admin, community=community, role=CommunityMember.ADMIN
    )


@pytest.mark.django_db()
def test_user_can_edit_own_post(user: User, post: Post) -> None:
    assert user.has_permission(post_id=post.id, permission_name="edit") is True


@pytest.mark.django_db()
def test_user_cannot_edit_others_post(post: Post, user_without_post: User) -> None:
    assert (
        user_without_post.has_permission(post_id=post.id, permission_name="edit")
        is False
    )


@pytest.mark.django_db()
def test_moderator_can_edit_post(
    moderator: User, post: Post, community_member_moderator: CommunityMember
) -> None:
    assert moderator.has_permission(post_id=post.id, permission_name="edit") is True


@pytest.mark.django_db()
def test_admin_can_edit_post(
    admin: User, post: Post, community_member_admin: CommunityMember
) -> None:
    assert admin.has_permission(post_id=post.id, permission_name="edit") is True


@pytest.mark.django_db()
def test_user_without_permission(user: User, post: Post) -> None:
    assert (
        user.has_permission(post_id=post.id, permission_name="nonexistent_permission")
        is False
    )
