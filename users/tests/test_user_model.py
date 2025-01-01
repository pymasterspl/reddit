import io
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.test import Client
from django.urls import reverse_lazy
from django.utils import timezone
from PIL import Image

from users.models import Profile, SocialLink, UserSettings

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
    assert admin_user.nickname == "admin_user"
    assert admin_user.email == "admin_user@example.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.check_password(admin_user.plain_password) is True
    created_user = User.objects.filter(email="admin_user@example.com").first()
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
    user.profile.avatar = avatar
    user.profile.save()
    user.save()
    processed_avatar = Image.open(user.profile.avatar)
    assert processed_avatar.size == (32, 32)


@pytest.mark.django_db()
def test_get_avatar_url(user: User) -> None:
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")


@pytest.mark.django_db()
def test_avatar_file_size_validation(user: User) -> None:
    image = Image.new("RGB", (1000, 1000), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    oversized_image = image_io.getvalue() + b"a" * (2 * 1024 * 10024)
    avatar = SimpleUploadedFile("oversized_avatar.jpg", oversized_image, content_type="image/jpeg")
    user.profile.avatar = avatar
    user.profile.bio = "test"
    user.profile.gender = "M"
    with pytest.raises(ValidationError) as excinfo:
        user.profile.full_clean()

    assert "File size must not exceed 2.00 MB." in str(excinfo)


@pytest.mark.django_db()
def test_process_banner(user: User) -> None:
    image = Image.new("RGB", (1000, 1000), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)
    banner = SimpleUploadedFile("test_banner.jpg", image_io.read(), content_type="image/jpeg")
    user.profile.banner = banner
    user.profile.save()
    user.save()
    processed_banner = Image.open(user.profile.banner)
    assert processed_banner.size == (300, 100)


@pytest.mark.django_db()
def test_get_banner_url(user: User) -> None:
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")


@pytest.mark.django_db()
def test_banner_file_size_validation(user: User) -> None:
    image = Image.new("RGB", (1000, 1000), color=(73, 109, 137))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    oversized_image = image_io.getvalue() + b"a" * (2 * 1024 * 10024)
    banner = SimpleUploadedFile("oversized_banner.jpg", oversized_image, content_type="image/jpeg")
    user.profile.banner = banner
    user.profile.bio = "test"
    user.profile.gender = "M"
    with pytest.raises(ValidationError) as excinfo:
        user.profile.full_clean()

    assert "File size must not exceed 0.49 MB." in str(excinfo)


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
    assert user_1.usersettings
    assert user_2.usersettings


@pytest.mark.django_db()
def test_language(user: User) -> None:
    user.usersettings.content_lang = "en"
    assert user.usersettings.get_content_lang_display() == "English"


@pytest.mark.django_db()
def test_location(user: User) -> None:
    for code, location in zip(
        ["AQ", "BR", "PL", "US", "FR", "AU", "JP", "UG", "TR"],
        ["Antarctica", "Brazil", "Poland", "United States", "France", "Australia", "Japan", "Uganda", "Türkiye"],
        strict=True,
    ):
        user.usersettings.location = code
        assert user.usersettings.get_location_display() == location


@pytest.mark.django_db()
def test_non_existing_locaton(user: User) -> None:
    user.usersettings.location = "XX"
    with pytest.raises(ValidationError) as exception_info:
        user.usersettings.clean_fields()
    assert "location" in exception_info.value.error_dict


@pytest.mark.django_db()
def test_language_location_there_are_some_defaults(user: User) -> None:
    location = user.usersettings.location
    language = user.usersettings.content_lang
    assert location
    assert language


@pytest.mark.django_db()
def test_user_deletion(user: "User") -> None:
    profile_id = user.profile.id
    usersettings_id = user.usersettings.id
    user.delete()
    assert not Profile.objects.filter(id=profile_id)
    assert not UserSettings.objects.filter(id=usersettings_id)


@pytest.mark.django_db()
def test_cascade_profile_sociallink_deletion(user: "User") -> None:
    profile_id = user.profile.id
    sociallink = SocialLink.objects.create(
        profile=user.profile, name="facebook", url="https://www.facebook.com/username.27"
    )
    sociallink_id = sociallink.id
    user_id = user.id
    user.save()
    assert user.profile.sociallink
    user.delete()
    assert not User.objects.filter(id=user_id).exists()
    assert not Profile.objects.filter(id=profile_id).exists()
    assert not SocialLink.objects.filter(id=sociallink_id).exists()


@pytest.mark.django_db()
def test_deactivate_user_sets_fields_correctly(user: User) -> None:
    user.deactivate()
    user.refresh_from_db()
    assert not user.is_active
    assert user.deactivated_at is not None
    assert user.reactivate_until > timezone.now()


@pytest.mark.django_db()
def test_cant_anonymize_active_user(user: User) -> None:
    user.anonymize_account()
    user.refresh_from_db()
    assert user.nickname == "test_user"
    assert user.is_active


@pytest.mark.django_db()
def test_anonymize_user_with_related_models_successfully(inactive_user: User) -> None:
    user = inactive_user
    settings, _ = UserSettings.objects.get_or_create(user=user)
    profile, _ = Profile.objects.get_or_create(user=user)
    social_link, _ = SocialLink.objects.get_or_create(profile=profile)
    user.anonymize_account()
    user.refresh_from_db()
    assert user.nickname.startswith("deleted_user_")
    assert user.anonymized_at
    assert not user.is_active
    assert not user.profile.banner
    assert user.profile.bio == ""
    assert not user.profile.avatar
    with pytest.raises(UserSettings.DoesNotExist):
        settings.refresh_from_db()
    with pytest.raises(SocialLink.DoesNotExist):
        social_link.refresh_from_db()


@pytest.mark.django_db()
def test_cannot_anonymize_user_with_future_reactivate_date(inactive_user: User) -> None:
    future_date = timezone.now() + timezone.timedelta(days=7)
    inactive_user.reactivate_until = future_date
    inactive_user.save()
    inactive_user.anonymize_account()
    inactive_user.refresh_from_db()
    assert inactive_user.nickname == "inactive_user"
    assert inactive_user.email == "inactive_user@example.com"
    assert inactive_user.reactivate_until == future_date


@pytest.mark.django_db()
@patch("users.models.default_storage")
def test_delete_avatar(mock_storage: MagicMock, user: User) -> None:
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = io.BytesIO()
    image.save(image_file, format="JPEG")
    image_file.seek(0)
    profile = user.profile
    profile.avatar = ContentFile(image_file.read(), "test_avatar.jpg")
    profile.save()
    assert profile.avatar.name.startswith("users_avatars/test_avatar")
    mock_storage.exists.return_value = True
    mock_storage.delete.return_value = None
    avatar_name = profile.avatar.name
    profile.delete_avatar()
    mock_storage.exists.assert_called_once_with(avatar_name)
    mock_storage.delete.assert_called_once_with(avatar_name)
    profile.refresh_from_db()
    assert not profile.avatar


@pytest.mark.django_db()
@patch("users.models.default_storage")
def test_delete_banner(mock_storage: MagicMock, user: User) -> None:
    image = Image.new("RGB", (100, 100), color=(255, 0, 0))
    image_file = io.BytesIO()
    image.save(image_file, format="JPEG")
    image_file.seek(0)
    profile = user.profile
    profile.banner = ContentFile(image_file.read(), "test_banner.jpg")
    profile.save()
    assert profile.banner.name.startswith("users_banners/test_banner")
    mock_storage.exists.return_value = True
    mock_storage.delete.return_value = None
    banner_name = profile.banner.name
    profile.delete_banner()
    mock_storage.exists.assert_called_once_with(banner_name)
    mock_storage.delete.assert_called_once_with(banner_name)
    profile.refresh_from_db()
    assert not profile.banner
