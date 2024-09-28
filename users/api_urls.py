from django.urls import include, path
from .api_views import MyProfileAPIView, ProfileAPIView, MyUserSettingsAPIView


urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("my-profile/", MyProfileAPIView.as_view(), name="my_profile"),
    path("profile/<int:pk>/", ProfileAPIView.as_view(), name="profile"),
    path("my-settings/", MyUserSettingsAPIView.as_view(), name="my_user_settings"),
]

"""
dj_rest_auth.urls below:

# URLs that do not require a session or valid token
path('password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
path('login/', LoginView.as_view(), name='rest_login'),

# URLs that require a user to be logged in with a valid session / token.
path('logout/', LogoutView.as_view(), name='rest_logout'),
path('user/', UserDetailsView.as_view(), name='rest_user_details'),
path('password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
"""
