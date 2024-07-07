from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

from .views import (
    AccountSettingsView,
    ActivateUser,
    CustomLogoutView,
    HomeView,
    LoginUserView,
    ProfileSettingsView,
    UserEditView,
    UserProfileView,
    UserRegistrationView,
)

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/edit/", UserEditView.as_view(), name="edit_profile"),
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("logout-confirmation/", TemplateView.as_view(template_name="users/logout.html"), name="logout_confirmation"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("activate/<str:uidb64>/<str:token>", ActivateUser.as_view(), name="activate-account"),
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
    path("settings/profile/", ProfileSettingsView.as_view(), name="profile_settings"),
    path("settings/account/", AccountSettingsView.as_view(), name="account_settings"),
]
