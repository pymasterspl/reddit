from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User

FieldsetsType = tuple[tuple[None, dict[str, str | tuple[str]]]]


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    list_display: list[str] = DjangoUserAdmin.list_display[1:] + ("is_online", "last_activity_ago")
    ordering: tuple[str] = ("email",)
    fieldsets: FieldsetsType = ()
    add_fieldsets: FieldsetsType = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
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
