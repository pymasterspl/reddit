from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView, TemplateView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import FormView

from core.models import User

from .forms import UserRegistrationForm
from .tokens import account_activation_token


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
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        protocol = "https" if self.request.is_secure() else "http"
        current_site = get_current_site(self.request)
        activation_link = reverse("activate-account", kwargs={"uidb64": uid, "token": token})
        full_activation_link = f"{protocol}://{current_site.domain}{activation_link}"
        send_mail(
            "Confirm your registration",
            f"Please click on the following link to confirm your registration " f"{activation_link}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
            html_message=render_to_string(
                "users/account_activation_email.html",
                {
                    "user": user,
                    "activation_link": full_activation_link,
                },
            ),
        )
        messages.success(
            self.request,
            f"Account created for {user.email}! " f"Please confirm your email to activate " f"your account.",
        )
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
                user.save()
                messages.success(request, "Your account has been activated, you can now login!")

                return redirect("login")
            return render(request, "users/account_activation_invalid.html")
        except User.DoesNotExist:
            messages.error(request, "Invalid activation link or account already activated!")
            return redirect("home-page")


class ProfileSettingsView(TemplateView):
    # Work on this view is in progress
    template_name = "users/profile_settings.html"


class AccountSettingsView(TemplateView):
    # Work on this view is in progress
    template_name = "users/account_settings.html"
