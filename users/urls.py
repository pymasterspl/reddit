from django.urls import path
from django.views.generic import TemplateView

from .views import CustomLogoutView, HomeView, LoginUserView, UserRegistrationView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout-confirmation/", TemplateView.as_view(template_name="users/logout.html"), name="logout_confirmation"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", UserRegistrationView.as_view(), name="register"),
]
