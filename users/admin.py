from typing import ClassVar

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from users.models import Profile, User, UserSettings
from users.tokens import account_activation_token

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

    def reactivate_user_view(self: "CustomUserAdmin", request: HttpRequest, user_id: str) -> HttpResponseRedirect:
        user = get_object_or_404(User, pk=user_id)
        if user.is_active:
            self.message_user(request, "User is already active. No reactivation needed.", messages.WARNING)
            return redirect(reverse("admin:users_user_change", args=[user.id]))
        if user.anonymized_at:
            self.message_user(request, "Cannot reactivate an anonymized user.", messages.ERROR)
            return redirect(reverse("admin:users_user_changelist"))
        if not user.reactivate_until or user.reactivate_until <= timezone.now():
            self.message_user(request, "Reactivation time has expired or is not set.", messages.ERROR)
            return redirect(reverse("admin:users_user_changelist"))
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        protocol = "https" if request.is_secure() else "http"
        current_site = get_current_site(request)
        activation_link = reverse("activate-account", kwargs={"uidb64": uid, "token": token})
        full_activation_link = f"{protocol}://{current_site.domain}{activation_link}"
        send_mail(
            "Confirm account reactivation",
            f"Please click on the following link to confirm account reactivation: {full_activation_link}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
            html_message=render_to_string(
                "users/reactivate_account_email.html",
                {
                    "user": user,
                    "activation_link": full_activation_link,
                },
            ),
        )
        self.message_user(
            request,
            f"The reactivation link has been sent successfully to {user.email} !",
            messages.SUCCESS,
        )
        return redirect("admin:users_user_changelist")

    def change_view(
        self: "CustomUserAdmin",
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict | None = None,
    ) -> HttpResponseRedirect:
        extra_context = extra_context or {}
        if self.show_reactivate_condition(object_id, request):
            reactivate_url = reverse("admin:reactivate_user", args=[object_id])
            extra_context.update(
                {
                    "show_reactivate_account": True,
                    "reactivate_url": reactivate_url,
                }
            )
        else:
            extra_context["show_reactivate_account"] = False
        return super().change_view(request, object_id, form_url, extra_context)

    def show_reactivate_condition(self: "CustomUserAdmin", obj_id: str, request: HttpRequest) -> bool:
        obj = self.get_object(request, obj_id)
        return bool(obj and not obj.is_active and not obj.anonymized_at and obj.reactivate_until > timezone.now())

    def get_urls(self: "CustomUserAdmin") -> list[path]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/change/reactivate/",
                self.admin_site.admin_view(self.reactivate_user_view),
                name="reactivate_user",
            )
        ]
        return custom_urls + urls
