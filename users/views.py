from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, TemplateView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.timezone import now
from django.views import View
from django.views.generic import DetailView, FormView

from core.models import User

from .forms import (
    ConfirmDeleteAccountForm,
    EmailChangeForm,
    UserForm,
    UserProfileForm,
    UserRegistrationForm,
    UserSettingsForm,
)
from .models import Profile, UserSettings
from .tokens import account_activation_token, email_change_token
from .utils import user_creation


class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/profile_overview.html"
    context_object_name = "user"
    login_url = "login"

    def get_object(self: "UserProfileView") -> User:
        return self.request.user


class HomeView(TemplateView):
    template_name = "users/home.html"


class LoginUserView(LoginView):
    redirect_authenticated_user = True
    template_name = "users/login.html"

    def get_success_url(self: "LoginUserView") -> str:
        return reverse_lazy("home-page")


class UserRegistrationView(FormView):
    template_name = "users/registration.html"
    form_class = UserRegistrationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("home-page")

    def form_valid(self: "UserRegistrationView", form: UserRegistrationForm) -> HttpResponse:
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        user_creation(user, "activate-account", self.request)
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = "login"

    def dispatch(self: "LogoutView", request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]) -> HttpResponse:
        messages.add_message(request, messages.SUCCESS, "You have successfully logged out.")
        return super().dispatch(request, *args, **kwargs)


class ActivateUser(View):
    def get(self: "ActivateUser", request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, is_active=False)
            if account_activation_token.check_token(user, token):
                user.is_active = True
                user.deactivated_at = None
                user.reactivate_until = None
                user.save()
                messages.success(request, "Your account has been activated, you can now login!")

                return redirect("login")
            return render(request, "users/account_activation_invalid.html")
        except User.DoesNotExist:
            messages.error(request, "Invalid activation link or account already activated!")
            return redirect("home-page")


class ProfileSettingsView(LoginRequiredMixin, FormView):
    model = Profile
    template_name = "users/profile_settings.html"
    form_class = UserProfileForm
    success_url = reverse_lazy("profile_settings")
    login_url = "login"

    def get_form(self: "ProfileSettingsView") -> dict[str, Any]:
        return {
            "user_form": UserForm(instance=self.request.user),
            "profile_form": self.form_class(instance=self.request.user.profile),
        }

    def form_valid(self: "ProfileSettingsView", form: dict[str, Any]) -> HttpResponse:
        user_form = form["user_form"]
        profile_form = form["profile_form"]
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(self.request, "Your profile settings have been updated successfully!")
            return super().form_valid(form)
        return self.form_invalid(form)

    def post(self: "ProfileSettingsView", request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]) -> HttpResponse:  # noqa: ARG002
        with transaction.atomic():
            form = self.get_form()
            form["user_form"] = UserForm(request.POST, instance=request.user)
            form["profile_form"] = self.form_class(request.POST, request.FILES, instance=request.user.profile)
            return self.form_valid(form)


class AccountSettingsView(LoginRequiredMixin, FormView):
    model = UserSettings
    template_name = "users/account_settings.html"
    form_class = UserSettingsForm
    success_url = reverse_lazy("account_settings")
    login_url = "login"

    def form_valid(self: "AccountSettingsView", form: UserSettingsForm) -> HttpResponse:
        form.save()
        messages.success(self.request, "Your account settings have been updated successfully!")
        return super().form_valid(form)

    def get_form_kwargs(self: "AccountSettingsView") -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user.usersettings
        return kwargs


class AccountDeleteView(LoginRequiredMixin, View):
    template_name = "users/delete_account.html"
    success_url = reverse_lazy("home")

    def get(self: "AccountDeleteView", request: HttpRequest) -> HttpResponse:
        form = ConfirmDeleteAccountForm(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self: "AccountDeleteView", request: HttpRequest) -> HttpResponse:
        form = ConfirmDeleteAccountForm(user=request.user, data=request.POST)
        if form.is_valid():
            request.user.deactivate()
            logout(request)
            messages.warning(
                request,
                "Your account has been deactivated. "
                f"You have {settings.ACCOUNT_EXPIRATION_TIME_IN_DAYS} days to reactivate it. "
                "After this time, your account will be permanently deleted. "
                "To reactivate your account, contact our support. "
                "Thank you for using our service! We hope to see you again soon!",
            )
            return redirect(self.success_url)
        messages.error(request, "Password confirmation failed.")
        return render(request, self.template_name, {"form": form})


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "users/password_change.html"
    success_url = reverse_lazy("account_settings")
    form_class = PasswordChangeForm

    def form_valid(self: "CustomPasswordChangeView", form: "PasswordChangeForm") -> HttpResponse:
        user = self.request.user
        send_mail(
            "Password change",
            "Your password has been changed successfully. If you did not make this change, please contact our support.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        messages.success(self.request, "Your password has been changed successfully!")

        return super().form_valid(form)


class EmailChangeView(LoginRequiredMixin, FormView):
    template_name = "users/email_change.html"
    success_url = reverse_lazy("account_settings")
    form_class = EmailChangeForm

    def get_form_kwargs(self: "EmailChangeView") -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self: "EmailChangeView", form: EmailChangeForm) -> HttpResponse:
        if form.is_valid():
            self.request.user.pending_email = form.cleaned_data["new_email"]
            self.request.user.pending_email_created = now()
            self.request.user.save()
            uid = urlsafe_base64_encode(force_bytes(self.request.user.pk))
            token = email_change_token.make_token(self.request.user)
            protocol = "https" if self.request.is_secure() else "http"
            current_site = get_current_site(self.request)
            activation_link = reverse("confirm-email-change", kwargs={"uidb64": uid, "token": token})
            full_activation_link = f"{protocol}://{current_site.domain}{activation_link}"
            send_mail(
                f"Confirm your email changing to {form.cleaned_data['new_email']} ",
                f"Please click on the following link to confirm your email change " f"{activation_link}",
                settings.EMAIL_HOST_USER,
                [self.request.user.email],
                fail_silently=False,
                html_message=render_to_string(
                    "users/confirm_email_change.html",
                    {
                        "user": self.request.user,
                        "activation_link": full_activation_link,
                    },
                ),
            )
            messages.success(self.request, "Your email change request processed!")
            return super().form_valid(form)
        return self.form_invalid(form)


class ConfirmEmailChange(View):
    def get(self: "ConfirmEmailChange", request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if email_change_token.check_token(user, token) and not email_change_token.is_token_expired(user):
                user.email = user.pending_email
                user.pending_email = None
                user.pending_email_created = None
                user.save()
                messages.success(request, "Your email has been changed!")

                return redirect("login")
            return render(request, "users/confirm_email_change_invalid.html")
        except User.DoesNotExist:
            messages.error(request, "Invalid confirmation link or email already changed!")
            return redirect("home-page")
