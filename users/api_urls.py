from rest_framework.urls import path

from .api_views import UserAPIRegistration

urlpatterns = [
    path("register/", UserAPIRegistration.as_view(), name="api-user-registration"),
]
