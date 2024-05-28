from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView

from .views import HomeView, LoginUserView, UserRegistrationView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout-confirmation/", TemplateView.as_view(template_name="users/logout"), name="logout_confirmation"),
    path("logout/", LogoutView.as_view(template_name="users/logout.html", next_page="login"), name="logout"),
    path("register/", UserRegistrationView.as_view(), name="register"),
]
