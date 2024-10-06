import pytest
from django.contrib import admin

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


def test_user_profile_inline_user(model_admin: admin.ModelAdmin) -> None:
    inlines = model_admin.inlines
    assert ProfileAdmin in inlines
    profile_inline = next(inline for inline in inlines if inline == ProfileAdmin)
    assert profile_inline is not None
    assert profile_inline.model == Profile
    assert profile_inline.verbose_name == "Profile"
    assert profile_inline.extra == 3
