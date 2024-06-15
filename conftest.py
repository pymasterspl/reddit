import secrets
import string
from collections.abc import Generator

import pytest
from django.contrib.auth import get_user_model

from core.models import Community, Post

User = get_user_model()


def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    secure_random = secrets.SystemRandom()
    return "".join(secure_random.choice(characters) for _ in range(length))


@pytest.fixture()
def generated_password() -> str:
    return generate_random_password()


@pytest.fixture()
def user_model() -> type[get_user_model()]:
    return get_user_model()


@pytest.fixture()
def user(generated_password: str) -> User:
    user = User.objects.create_user(email="test@example.com", nickname="test_user", password=generated_password)
    user.plain_password = generated_password
    return user


@pytest.fixture()
def another_user(generated_password: str) -> User:
    user = User.objects.create_user(
        email="another_user@example.com", nickname="another_user", password=generated_password,
    )
    user.plain_password = generated_password
    return user


@pytest.fixture()
def admin_user(generated_password: str) -> User:
    admin_user = User.objects.create_superuser(email="admin@example.com", nickname="admin", password=generated_password)
    admin_user.plain_password = generated_password
    return admin_user


@pytest.fixture()
def community(user: User) -> Generator[Community, None, None]:
    return Community.objects.create(author=user, name="Test Community")


@pytest.fixture()
def post(user: User, community: Community) -> Generator[Post, None, None]:
    return Post.objects.create(
        author=user,
        community=community,
        title="Test Post",
        content="This is a test post",
    )
