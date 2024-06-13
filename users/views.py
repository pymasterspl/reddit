from typing import Any

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, LogoutView, TemplateView
from django.forms import Form
from django.http import HttpRequest, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView

from .forms import UserRegistrationForm


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
        form.save()
        username = form.cleaned_data.get("username")
        email = form.cleaned_data.get("email")
        messages.success(self.request, f"Account created for {username} with: {email}!")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = "login"

    def dispatch(self: "LogoutView", request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]) -> HttpResponse:
        messages.add_message(request, messages.SUCCESS, "You have successfully logged out.")
        return super().dispatch(request, *args, **kwargs)
