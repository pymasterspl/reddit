from unittest.mock import MagicMock

import pytest
from django.contrib.auth.hashers import make_password

from core.models import Community, CommunityMember, Post
from users.models import User


@pytest.fixture()
def moderator() -> User:
    return User.objects.create_user(
        email="moderator@example.com",
        nickname="moderator",
        password=make_password("password"),
    )


@pytest.fixture()
def community_member_moderator(moderator: User, community: Community) -> CommunityMember:
    return CommunityMember.objects.create(user=moderator, community=community, role=CommunityMember.MODERATOR)


@pytest.fixture()
def community_member_admin(admin_user: User, community: Community) -> CommunityMember:
    return CommunityMember.objects.create(user=admin_user, community=community, role=CommunityMember.ADMIN)


@pytest.mark.django_db()
def test_check_permission_post_edit_author(user: User, post: Post) -> None:
    assert user._User__check_permission_post_edit(post.id) is True  # noqa: SLF001


@pytest.mark.django_db()
def test_check_permission_post_edit_moderator(
    moderator: User, post: Post, community_member_moderator: CommunityMember
) -> None:
    assert moderator._User__check_permission_post_edit(post.id) is True  # noqa: SLF001


@pytest.mark.django_db()
def test_check_permission_post_edit_not_a_moderator(moderator: User, post2: Post) -> None:
    assert (
        moderator._User__check_permission_post_edit(post2.id) is False  # noqa: SLF001
    )


@pytest.mark.django_db()
def test_check_permission_post_edit_admin(
    admin_user: User, post: Post, community_member_admin: CommunityMember
) -> None:
    assert admin_user._User__check_permission_post_edit(post.id) is True  # noqa: SLF001


@pytest.mark.django_db()
def test_check_permission_post_edit_not_an_admin(admin_user: User, post2: Post) -> None:
    assert (
        admin_user._User__check_permission_post_edit(post2.id) is False  # noqa: SLF001
    )


@pytest.mark.django_db()
def test_check_permission_post_edit_user_not_post_owner(another_user: User, post: Post) -> None:
    assert (
        another_user._User__check_permission_post_edit(post.id) is False  # noqa: SLF001
    )


@pytest.mark.django_db()
def test_check_permission_post_edit_non_existent_post(user: User) -> None:
    assert user._User__check_permission_post_edit(99999) is False  # noqa: SLF001


@pytest.mark.django_db()
def test_has_permission_calls_check_permission_post_edit(user: User, post: Post) -> None:
    mock = MagicMock()
    user._User__check_permission_post_edit = mock  # noqa: SLF001
    user.has_permission(post_id=post.id, permission_name="edit")
    mock.assert_called_once_with(post.id)


@pytest.mark.django_db()
def test_has_permission_integration(user: User, post: Post) -> None:
    assert user.has_permission(post_id=post.id, permission_name="edit") is True


@pytest.mark.django_db()
def test_user_cannot_edit_nonexistent_post(user: User) -> None:
    assert user.has_permission(post_id=9999, permission_name="edit") is False


@pytest.mark.django_db()
def test_user_can_edit_own_post(user: User, post: Post) -> None:
    assert user.has_permission(post_id=post.id, permission_name="edit") is True


@pytest.mark.django_db()
def test_has_permission_no_permission(user: User, post: Post) -> None:
    assert user.has_permission(post_id=post.id, permission_name="nonexistent_permission") is False
