from tkinter.font import names

from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

from core.profile_urls import profile_urlpatterns

from .views import (
    AccountDeleteView,
    AccountSettingsView,
    ActivateUser,
    ConfirmEmailChange,
    CustomLogoutView,
    CustomPasswordChangeView,
    EmailChangeView,
    HomeView,
    LoginUserView,
    ProfileSettingsView,
    UserProfileView,
    UserRegistrationView,
    Enable2FAView,
    Disable2FAView,

)

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/edit/profile/", ProfileSettingsView.as_view(), name="profile_settings"),
    path("profile/edit/account/", AccountSettingsView.as_view(), name="account_settings"),
    path("profile/edit/password/", CustomPasswordChangeView.as_view(), name="password_change"),
    path("profile/edit/email/", EmailChangeView.as_view(), name="email_change"),
    path("profile/enable-2fa/", Enable2FAView.as_view(), name="enable_2fa"),
    path("profile/disable-2fa/", Disable2FAView.as_view(), name="disable_2fa"),
    path("profile/delete-account", AccountDeleteView.as_view(), name="delete_account"),
    *profile_urlpatterns,
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout-confirmation/", TemplateView.as_view(template_name="users/logout.html"), name="logout_confirmation"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("activate/<str:uidb64>/<str:token>", ActivateUser.as_view(), name="activate-account"),
    path(
        "email-change-confirmation/<str:uidb64>/<str:token>", ConfirmEmailChange.as_view(), name="confirm-email-change"
    ),
    path(
        "reset_password/",
        auth_views.PasswordResetView.as_view(template_name="users/reset_password.html"),
        name="reset_password",
    ),
    path(
        "reset_password_sent/",
        auth_views.PasswordResetDoneView.as_view(template_name="users/password_reset_sent.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>",
        auth_views.PasswordResetConfirmView.as_view(template_name="users/password_reset_form.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset_password_complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="users/password_reset_done.html"),
        name="password_reset_complete",
    ),
    path("google/", include("social_django.urls", namespace="social")),
]
