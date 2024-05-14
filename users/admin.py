from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User

FieldsetsType = tuple[tuple[None, dict[str, str | tuple[str]]]]


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    list_display: list[str] = DjangoUserAdmin.list_display[1:]
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
