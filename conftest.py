import secrets
import string
from collections.abc import Callable, Generator

import pytest
from django.contrib.auth import get_user_model

from core.models import Community, CommunityMember, Post

User = get_user_model()


def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    secure_random = secrets.SystemRandom()
    return "".join(secure_random.choice(characters) for _ in range(length))


@pytest.fixture()
def reusable_password() -> Callable[[], str]:
    def _generated_password() -> str:
        return generate_random_password()

    return _generated_password


@pytest.fixture()
def generated_password() -> str:
    return generate_random_password()


@pytest.fixture()
def user_model() -> type[get_user_model()]:
    return get_user_model()


@pytest.fixture()
def user(reusable_password: Callable[[], str]) -> User:
    password = reusable_password()
    user = User.objects.create_user(email="test@example.com", nickname="test_user", password=password)
    user.plain_password = password
    return user


@pytest.fixture()
def another_user(reusable_password: Callable[[], str]) -> User:
    """Use when user different than community author is needed."""
    password = reusable_password()
    user = User.objects.create_user(email="other_user@example.com", nickname="other_user", password=password)
    user.plain_password = password
    return user


@pytest.fixture()
def admin_user(generated_password: str) -> User:
    admin_user = User.objects.create_superuser(
        email="admin_user@example.com",
        nickname="admin_user",
        password=generated_password,
    )
    admin_user.plain_password = generated_password
    return admin_user


@pytest.fixture()
def community(user: User) -> Generator[Community, None, None]:
    # community is restricted by default
    return Community.objects.create(author=user, name="Test Community")


@pytest.fixture()
def community2(user: User) -> Generator[Community, None, None]:
    return Community.objects.create(author=user, name="Test Community2")

def non_authored_community() -> Community:
    return Community.objects.create(name="Test Community", is_active=True)


@pytest.fixture()
def restricted_community(user: User) -> Community:
    # community is restricted by default
    return Community.objects.create(
        name="Restricted Community", privacy=Community.RESTRICTED, is_active=True, author=user
    )


@pytest.fixture()
def private_community(user: User) -> Community:
    return Community.objects.create(name="Private Community", privacy=Community.PRIVATE, is_active=True, author=user)


@pytest.fixture()
def public_community(user: User) -> Community:
    return Community.objects.create(name="Private Community", privacy=Community.PUBLIC, is_active=True, author=user)


UsersWithMembersFixture = Callable[[int, Community], None]
CommunityWithMembersFixture = Callable[[int], Community]
CreateCommunitiesFixture = Callable[[int, int, str], list[Community]]


@pytest.fixture()
def create_users_with_members(reusable_password: Callable[[], str]) -> UsersWithMembersFixture:
    def _create_users_with_members(size: int, community: Community) -> None:
        for i in range(1, size + 1):
            user = User.objects.create_user(
                email=f"user_{i}@users.com", nickname=f"User_{i}", password=reusable_password()
            )
            CommunityMember.objects.create(community=community, user=user, role=CommunityMember.MEMBER)

    return _create_users_with_members


@pytest.fixture()
def public_community_with_members(
    public_community: Community, create_users_with_members: None
) -> CommunityWithMembersFixture:
    def _public_community_with_members(size: int) -> Community:
        create_users_with_members(size, public_community)
        return public_community

    return _public_community_with_members


@pytest.fixture()
def restricted_community_with_members(
    restricted_community: Community, create_users_with_members: None
) -> CommunityWithMembersFixture:
    def _restricted_community_with_members(size: int) -> Community:
        create_users_with_members(size, restricted_community)
        return restricted_community

    return _restricted_community_with_members


def create_posts(community: Community, count: int, start_idx: int = 1) -> list[Post]:
    return [
        Post.objects.create(
            author=community.author, community=community, title=f"Test Post {i}", content=f"This is a test post {i}"
        )
        for i in range(start_idx, start_idx + count)
    ]


@pytest.fixture()
def create_communities(user: User) -> CreateCommunitiesFixture:
    def _create_communties(count: int, posts_per_community: int, privacy: str = Community.PUBLIC) -> list[Community]:
        result = []
        for i in range(1, count + 1):
            community = Community.objects.create(author=user, name=f"Test community {i}", privacy=privacy)
            result.append(community)
            create_posts(community, count=posts_per_community, start_idx=(i - 1) * posts_per_community + 1)
        return result

    return _create_communties


@pytest.fixture()
def post(user: User, community: Community) -> Generator[Post, None, None]:
    return Post.objects.create(
        author=user,
        community=community,
        title="Test Post",
        content="This is a test post",
    )


@pytest.fixture()
def post2(user: User, community2: Community) -> Generator[Post, None, None]:
    return Post.objects.create(
        author=user,
        community=community2,
        title="Test Post2",
        content="This is a test post2",
    )


@pytest.fixture()
def comment(user: User, post: Post) -> Generator[Post, None, None]:
    return Post.objects.create(
        author=user,
        community=post.community,
        title="Test comment",
        content="This is a test comment",
        parent=post,
    )
