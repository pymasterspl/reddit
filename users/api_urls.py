from rest_framework.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .api_views import UserAPILogin, UserAPILogout, UserAPIRegistration

urlpatterns = [
    path("register/", UserAPIRegistration.as_view(), name="api-user-registration"),
    path("login/", UserAPILogin.as_view(), name="api-user-login"),
    path("logout/", UserAPILogout.as_view(), name="api-user-logout"),
    path("token-refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
]
