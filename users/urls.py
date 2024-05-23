from django.urls import path

from .views import HomeView, LoginUserView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginUserView.as_view(), name="login"),
]
