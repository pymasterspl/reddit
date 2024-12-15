from typing import ClassVar
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.safestring import mark_safe

from users.models import Profile, User, UserSettings
from django.utils.timezone import now
from django.urls import path
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import get_object_or_404

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
    list_display: tuple[str] = (
                                "nickname",
                                "email",
                                "is_staff",
                                "is_online",
                                "last_activity_ago",
                                "is_active",
                                "deactivated_at",
                                "reactivate_until",
                                "reactivate_user_link",
                                )
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

    def get_urls(self: "CustomUserAdmin") -> list[path]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/reactivate/",
                self.admin_site.admin_view(self.reactivate_user_view),
                name="reactivate_user",
            )
        ]
        return custom_urls + urls

    def reactivate_user_view(self: "CustomUserAdmin", request: HttpRequest, user_id: int) -> HttpResponseRedirect:
        user = get_object_or_404(User, pk=user_id)
        if not user.is_active:
            if user.reactivate_until and user.reactivate_until >= now():
                user.is_active = True
                user.deactivated_at = None
                user.reactivate_until = None
                user.save()
                self.message_user(request, f"User {user.email} reactivated successfully.", messages.SUCCESS)
            else:
                self.message_user(request, f"Cannot reactivate user {user.email} (grace period expired).", messages.ERROR)

        else:
            self.message_user(request, f"Cannot reactivate user {user.email} (already active).", messages.ERROR)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/users/user/"))

    def reactivate_user_link(self, obj: User):
        if not obj.is_active:
            return mark_safe(f'<a href="{obj.id}/reactivate/">Reactivate</a>')
        return "-"
    reactivate_user_link.short_description = "Reactivate Link"
