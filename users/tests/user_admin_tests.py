from unittest.mock import patch

import pytest
from django.contrib import admin
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

import users.models
from users.admin import CustomUserAdmin, ProfileAdmin, UserSettingAdmin
from users.models import Profile, User, UserSettings

FieldsetsType = tuple[tuple[None, dict[str, str | tuple[str]]]]


def get_registered_model_admin(model: users.models) -> admin.ModelAdmin:
    model_admin_class = admin.site.get_model_admin(model)

    if model_admin_class is None:
        message = f"No admin registered for model {model}"
        raise ValueError(message)
    return model_admin_class


@pytest.fixture()
def model_admin() -> admin.ModelAdmin:
    return get_registered_model_admin(User)


def test_admin_registered(model_admin: admin.ModelAdmin) -> None:
    assert isinstance(model_admin, CustomUserAdmin)


def test_fieldsets(model_admin: admin.ModelAdmin) -> None:
    assert model_admin.fieldsets == ()


def test_add_fieldsets(model_admin: admin.ModelAdmin) -> None:
    expected_fields: FieldsetsType = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "nickname",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    assert model_admin.add_fieldsets == expected_fields


def test_user_setting_inline_user(model_admin: admin.ModelAdmin) -> None:
    inlines = model_admin.inlines
    assert UserSettingAdmin in inlines
    user_setting_inline = next(inline for inline in inlines if inline == UserSettingAdmin)
    assert user_setting_inline.model == UserSettings
    assert user_setting_inline.verbose_name == "Settings"
    assert user_setting_inline.extra == 3
    assert user_setting_inline.can_delete is False


def test_user_profile_inline_user(model_admin: admin.ModelAdmin) -> None:
    inlines = model_admin.inlines
    assert ProfileAdmin in inlines
    profile_inline = next(inline for inline in inlines if inline == ProfileAdmin)
    assert profile_inline is not None
    assert profile_inline.model == Profile
    assert profile_inline.verbose_name == "Profile"
    assert profile_inline.extra == 3
    assert profile_inline.can_delete is False


def test_model_admin_is_correct_instance(model_admin: admin.ModelAdmin) -> None:
    assert hasattr(model_admin, "show_reactivate_condition")
    assert callable(model_admin.show_reactivate_condition)


@freeze_time("2025-01-01 12:00:00")
@pytest.mark.django_db()
def test_show_reactivate_condition_method_should_return_true_for_valid_conditions(
    model_admin: admin.ModelAdmin, user: User
) -> None:
    user.reactivate_until = timezone.now() + timezone.timedelta(seconds=1)
    user.is_active = False
    user.save()
    user.refresh_from_db()
    request = RequestFactory().get("/")
    assert model_admin.show_reactivate_condition(obj_id=user.id, request=request)


@freeze_time("2025-01-01 12:00:00")
@pytest.mark.django_db()
def test_reactivate_user_view_redirects_to_change_form(model_admin: admin.ModelAdmin, user: User) -> None:
    user.is_active = False
    user.reactivate_until = timezone.now() + timezone.timedelta(seconds=1)
    user.save()
    user.refresh_from_db()
    factory = RequestFactory()
    request = factory.get(f"/admin/users/user/{user.id}/reactivate/")
    with patch.object(model_admin, "message_user", return_value=None):
        response = model_admin.reactivate_user_view(request, user.id)
    assert len(mail.outbox) == 1
    assert response.status_code == 302
    assert response.url == reverse("admin:users_user_changelist")


@pytest.mark.django_db()
def test_user_already_active(model_admin: admin.ModelAdmin, user: User) -> None:
    request = RequestFactory().get("/")
    with patch.object(model_admin, "message_user", return_value=None):
        response = model_admin.reactivate_user_view(request, user.id)
    assert len(mail.outbox) == 0
    assert response.status_code == 302
    assert response.url == reverse("admin:users_user_change", args=[user.id])


@pytest.mark.django_db()
def test_anonymized_user_cannot_be_reactivated(model_admin: admin.ModelAdmin, user: User) -> None:
    user.anonymized_at = timezone.now()
    user.is_active = False
    user.save()
    user.refresh_from_db()
    request = RequestFactory().get("/")
    with patch.object(model_admin, "message_user", return_value=None):
        response = model_admin.reactivate_user_view(request, user.id)
    assert len(mail.outbox) == 0
    assert response.status_code == 302
    assert response.url == reverse("admin:users_user_changelist")


@freeze_time("2025-01-01 12:00:00")
@pytest.mark.django_db()
def test_expired_reactivation_time(model_admin: admin.ModelAdmin, user: User) -> None:
    user.reactivate_until = timezone.now() - timezone.timedelta(seconds=1)
    user.is_active = False
    user.save()
    user.refresh_from_db()
    request = RequestFactory().get("/")
    with patch.object(model_admin, "message_user", return_value=None):
        response = model_admin.reactivate_user_view(request, user.id)
    assert len(mail.outbox) == 0
    assert response.status_code == 302
    assert response.url == reverse("admin:users_user_changelist")
