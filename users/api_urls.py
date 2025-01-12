from rest_framework.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .api_views import (
    ActivateAPIUser,
    CurrentUserProfileAPIView,
    CurrentUserSettingsAPIView,
    UserAPILogin,
    UserAPILogout,
    UserAPIRegistration,
    UserRetrieveAPIView,
)

urlpatterns = [
    path("register/", UserAPIRegistration.as_view(), name="api-user-registration"),
    path("login/", UserAPILogin.as_view(), name="api-user-login"),
    path("token-refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("activate/<str:uidb64>/<str:token>", ActivateAPIUser.as_view(), name="api-activate-account"),
    path("profile/", CurrentUserProfileAPIView.as_view(), name="api-user-profile"),
    path("settings/", CurrentUserSettingsAPIView.as_view(), name="api-user-settings"),
    path("logout/", UserAPILogout.as_view(), name="api-user-logout"),
    path("<str:nickname>/", UserRetrieveAPIView.as_view(), name="api-user"),
]
