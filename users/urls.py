from django.urls import path

from .views import HomeView, LoginUserView, UserRegistrationView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("register/", UserRegistrationView.as_view(), name="register"),
]
