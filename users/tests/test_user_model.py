import io

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.test import Client
from django.urls import reverse_lazy
from PIL import Image

from users.models import Profile, UserSettings

User = get_user_model()
HTTP_SUCCESS = 200


@pytest.mark.django_db()
def test_create_user(user: User) -> None:
    assert user.nickname == "test_user"
    assert user.email == "test@example.com"
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.check_password(user.plain_password) is True
    created_user = User.objects.filter(email="test@example.com").first()
    assert created_user is not None


@pytest.mark.django_db()
def test_create_superuser(admin_user: User) -> None:
    assert admin_user.nickname == "admin"
    assert admin_user.email == "admin@example.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.check_password(admin_user.plain_password) is True
    created_user = User.objects.filter(email="admin@example.com").first()
    assert created_user is not None


@pytest.mark.django_db()
def test_create_user_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_user(email="", nickname="nickname", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_missing_email(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Users must have an email address"):
        User.objects.create_superuser(email="", nickname="admin", password=generated_password)


@pytest.mark.django_db()
def test_create_superuser_not_staff(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
        User.objects.create_superuser(
            email="admin@example.com",
            nickname="admin",
            password=generated_password,
            is_staff=False,
        )


@pytest.mark.django_db()
def test_create_superuser_not_superuser(generated_password: str) -> None:
    with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
        User.objects.create_superuser(
            email="admin@example.com",
            nickname="admin",
            password=generated_password,
            is_superuser=False,
        )


def test_login_user_view_get(client: Client) -> None:
    response = client.get(reverse_lazy("login"))
    assert response.status_code == HTTP_SUCCESS
    assert b"Log in" in response.content


@pytest.mark.django_db()
def test_process_avatar(user: User) -> None:
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)
    avatar = SimpleUploadedFile("test_avatar.jpg", image_io.read(), content_type="image/jpeg")
    user.avatar = avatar
    user.save()
    processed_avatar = Image.open(user.avatar)
    assert processed_avatar.size == (32, 32)


@pytest.mark.django_db()
def test_get_avatar_url(user: User) -> None:
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")


@pytest.mark.django_db()
def test_nickname_is_null(user: User) -> None:
    user.nickname = None
    with pytest.raises(IntegrityError):
        user.save()


@pytest.mark.django_db()
def test_blank_fields_user_create() -> None:
    user_1 = User.objects.create(nickname="", email="", password="")
    with pytest.raises(ValidationError) as exception_info:
        user_1.clean_fields()
    error_dict = exception_info.value.error_dict
    assert "nickname" in error_dict
    assert "email" in error_dict
    assert "password" in error_dict


@pytest.mark.django_db()
@pytest.mark.parametrize("null_field_name", ["nickname", "email", "password"])
def test_null_fields_user_create(user: User, null_field_name: str) -> None:
    setattr(user, null_field_name, None)
    with pytest.raises(IntegrityError):
        user.save()


@pytest.mark.django_db()
def test_duplicate_user_email(generated_password: str) -> None:
    User.objects.create(email="user@bbb.com", password=generated_password)
    with pytest.raises(IntegrityError):
        User.objects.create(email="user@bbb.com", password=generated_password)


@pytest.mark.django_db()
def test_duplicate_user_nickname(generated_password: str) -> None:
    User.objects.create(nickname="user", email="some_user@some.com", password=generated_password)
    with pytest.raises(IntegrityError):
        User.objects.create(nickname="user", email="other_user@other.com", password=generated_password)


@pytest.mark.django_db()
def test_user_signals(generated_password: str) -> None:
    user_1 = User.objects.create(nickname="User1", email="user@bbb.com", password=generated_password)
    user_2 = User.objects.create(nickname="User2", email="user@aaa.com", password=generated_password)
    assert user_1.nickname == "User1"
    assert user_2.nickname == "User2"
    assert user_1.email == "user@bbb.com"
    assert user_2.email == "user@aaa.com"
    assert user_1.profile
    assert user_2.profile
    assert user_1.user_settings
    assert user_2.user_settings


@pytest.mark.django_db()
def test_language(user: User) -> None:
    user.user_settings.content_lang = "en"
    assert user.user_settings.get_content_lang_display() == "English"


@pytest.mark.django_db()
def test_location(user: User) -> None:
    for code, location in zip(
        ["AQ", "BR", "PL", "US", "FR", "AU", "JP", "UG", "TR"],
        ["Antarctica", "Brazil", "Poland", "United States", "France", "Australia", "Japan", "Uganda", "Türkiye"],
        strict=True,
    ):
        user.user_settings.location = code
        assert user.user_settings.get_location_display() == location


@pytest.mark.django_db()
def test_non_existing_locaton(user: User) -> None:
    user.user_settings.location = "XX"
    with pytest.raises(ValidationError) as exception_info:
        user.user_settings.clean_fields()
    assert "location" in exception_info.value.error_dict


@pytest.mark.django_db()
def test_language_location_there_are_some_defaults(user: User) -> None:
    location = user.user_settings.location
    language = user.user_settings.content_lang
    assert location
    assert language


@pytest.mark.django_db()
def test_deletion(user):
    profile_id = user.profile.id
    user_settings_id = user.user_settings.id
    user.delete()
    assert not Profile.objects.filter(id=profile_id).exists()
    assert not UserSettings.objects.filter(id=user_settings_id).exists()

@pytest.mark.django_db()
def test_deletion_2(user):
    user.profile.delete()
    user.user_settings.delete()
    user.save()
