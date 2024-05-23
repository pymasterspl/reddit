from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, TemplateView
from django.forms import Form
from django.http import HttpResponse
from django.urls import reverse_lazy


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
