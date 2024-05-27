from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, TemplateView
from django.forms import Form
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import UserRegistrationForm


class HomeView(TemplateView):
    template_name = "users/home.html"


class LoginUserView(LoginView):
    redirect_authenticated_user = True
    template_name = "users/login.html"

    def get_success_url(self: "LoginUserView") -> str:
        return reverse_lazy("home-page")

    def form_valid(self: "LoginUserView", form: Form) -> HttpResponse:
        valid = super().form_valid(form)
        email, password = form.cleaned_data.get("email"), form.cleaned_data.get("password1")
        user = authenticate(email=email, password=password)
        login(self.request, user)
        return valid


class UserRegistrationView(FormView):
    template_name = "users/registration.html"
    form_class = UserRegistrationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("home-page")

    def form_valid(self: "UserRegistrationView", form: UserRegistrationForm) -> HttpResponse:
        form.save()
        email = form.cleaned_data.get("email")
        messages.success(self.request, f"Account created for {email}!")
        return super().form_valid(form)
