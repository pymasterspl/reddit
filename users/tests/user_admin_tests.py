import pytest
from django.contrib import admin

import users.models
from users.admin import CustomUserAdmin, ProfileAdmin, UserSettingAdmin
from users.models import User

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

    assert UserSettingAdmin in model_admin.inlines


def test_user_profile_inline_user(model_admin: admin.ModelAdmin) -> None:

    assert ProfileAdmin in model_admin.inlines
