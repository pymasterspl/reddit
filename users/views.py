from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, LogoutView, TemplateView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.forms import Form
from django.http import HttpRequest, HttpResponse, request
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import FormView
from django.utils.encoding import force_str

from .tokens import account_activation_token
from core.models import User
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
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_link = f"http://{self.request.get_host()}/{uid}/{token}/"
        current_site = get_current_site(self.request)
        send_mail(
            'Confirm your registration',
            f'Please click on the following link to confirm your registration {activation_link}',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
            html_message=render_to_string('users/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
        )
        messages.success(self.request, f"Account created for {user.email}! Please confirm your email to activate your account.")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = "login"

    def dispatch(self: "LogoutView", request: HttpRequest, *args: tuple, **kwargs: dict[str, Any]) -> HttpResponse:
        messages.add_message(request, messages.SUCCESS, "You have successfully logged out.")
        return super().dispatch(request, *args, **kwargs)


class ActivateUser(View):

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if account_activation_token.check_token(user, token):
                user.is_active = True
                user.save()
                messages.success(request,
                                 "Your account has been activated, you can now login!")

                return redirect('login')
            else:
                return render(request, 'users/account_activation_invalid.html')
        except User.DoesNotExist:
            messages.error(request, "Invalid activation link or account already activated!")
            return redirect('home-page')
