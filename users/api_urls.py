from rest_framework.urls import path

from .api_views import UserApiRegistration

urlpatterns = [
    path("registration/", UserApiRegistration.as_view(), name="api-user-registration"),
]
