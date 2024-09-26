import secrets
import io
import string
from collections.abc import Callable, Generator
from rest_framework.test import APIClient, APIRequestFactory
import pytest
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import Community, CommunityMember, Post
from users.models import Profile, SocialLink, UserSettings
from users.choices import FEMALE
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from pathlib import Path


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_request_factory():
    return APIRequestFactory()


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
    admin_user = User.objects.create_superuser(email="admin@example.com", nickname="admin", password=generated_password)
    admin_user.plain_password = generated_password
    return admin_user


@pytest.fixture()
def social_links_factory():
    # return _social
    def _social_links_factory(profile, count):
        for i in range(count):
            SocialLink.objects.create(
                name=f"social-{i}",
                url = "http://social-{i}.org",
                profile=profile),
    return _social_links_factory


@pytest.fixture()
def profile(social_links_factory) -> Profile:
    def _profile(user):
        user.profile.bio = "Lorem Ipsum"
        user.profile.gender=FEMALE
        user.profile.is_nsfw=False
        user.profile.is_followable=True
        user.profile.is_content_visible=True
        user.profile.is_communities_visible=True
        social_links_factory(user.profile, 3)
        user.profile.save()
        return user.profile
    return _profile


@pytest.fixture()
def usersettings():
    def _usersettings(user):
        user.usersettings.content_lang = "en"
        user.usersettings.is_beta = False
        user.usersettings.is_over_18 = False
        user.usersettings.save()
        return user.usersettings
    return _usersettings


@pytest.fixture()
def user_with_everything(user_with_avatar, usersettings, profile):
    usersettings(user_with_avatar)
    profile(user_with_avatar)
    return user_with_avatar


@pytest.fixture()
def create_avatar() -> SimpleUploadedFile:
    avatar_dir = Path(settings.MEDIA_ROOT) / "users_avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)
    base_filename = "test_avatar"

    avatar_path = Path(f"{avatar_dir}/{base_filename}.jpg")

    with Path.open(avatar_path, "wb") as f:
        f.write(img_io.read())

    with Path.open(avatar_path, "rb") as f:
        avatar = SimpleUploadedFile(name=avatar_path, content=f.read(), content_type="image/jpeg")

    yield avatar

    for file_path in avatar_dir.glob(f"{base_filename}*"):
        if Path.exists(file_path):
            Path.unlink(file_path)



@pytest.fixture()
def community(user: User) -> Generator[Community, None, None]:
    # community is restricted by default
    return Community.objects.create(author=user, name="Test Community")


@pytest.fixture()
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
def comment(user: User, post: Post) -> Generator[Post, None, None]:
    return Post.objects.create(
        author=user,
        community=post.community,
        title="Test comment",
        content="This is a test comment",
        parent=post,
    )
