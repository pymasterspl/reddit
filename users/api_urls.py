from rest_framework.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .api_views import (
    ActivateAPIUser,
    ProfileAPIView,
    UserAPILogin,
    UserAPILogout,
    UserAPIRegistration,
    UserRetrieveAPIView,
    UserSettingsAPIView,
)

urlpatterns = [
    path("register/", UserAPIRegistration.as_view(), name="api-user-registration"),
    path("login/", UserAPILogin.as_view(), name="api-user-login"),
    path("logout/", UserAPILogout.as_view(), name="api-user-logout"),
    path("token-refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("activate/<str:uidb64>/<str:token>", ActivateAPIUser.as_view(), name="api-activate-account"),
    path("profile/", ProfileAPIView.as_view(), name="api-user-profile"),
    path("settings/", UserSettingsAPIView.as_view(), name="api-user-settings"),
    path("<str:nickname>/", UserRetrieveAPIView.as_view(), name="api-user"),
]
