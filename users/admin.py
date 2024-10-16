from typing import ClassVar

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import Profile, User, UserSettings

FieldsetsType = tuple[tuple[None, dict[str, str | tuple[str]]]]


class UserSettingAdmin(admin.StackedInline):
    model = UserSettings
    verbose_name = "Settings"
    can_delete = False


class ProfileAdmin(admin.StackedInline):
    model = Profile
    verbose_name = "Profile"
    can_delete = False


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    inlines: ClassVar[list] = [UserSettingAdmin, ProfileAdmin]
    list_display: tuple[str] = ("nickname", "email", "is_staff", "is_online", "last_activity_ago")
    ordering: tuple[str] = ("email",)
    fieldsets: FieldsetsType = ()
    add_fieldsets: FieldsetsType = (
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
    def is_online(self: "CustomUserAdmin", obj: User) -> bool | str:
        return obj.is_online

    is_online.boolean = True
    is_online.short_description = "Online Status"
