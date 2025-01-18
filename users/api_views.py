from typing import Any

from django.contrib.auth import authenticate, login, logout
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from requests import Request
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Profile, User, UserSettings
from .serializers import ProfileSerializer, UserRegistrationSerializer, UserSerializer, UserSettingsSerializer
from .tokens import account_activation_token
from .utils import AuthenticatedView


class UserAPIRegistration(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer


class UserRetrieveAPIView(AuthenticatedView, RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "nickname"


class CurrentUserProfileAPIView(AuthenticatedView, RetrieveAPIView, UpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self: "CurrentUserProfileAPIView") -> UserSettings:
        return Profile.objects.select_related("user").get(user__id=self.request.user.id)


class CurrentUserSettingsAPIView(AuthenticatedView, RetrieveAPIView, UpdateAPIView):
    serializer_class = UserSettingsSerializer

    def get_object(self: "CurrentUserSettingsAPIView") -> UserSettings:
        return UserSettings.objects.select_related("user").get(user__id=self.request.user.id)


class UserAPILogin(TokenObtainPairView):
    def post(self: "UserAPILogin", request: Request, *args: tuple, **kwargs: dict[str, Any]) -> Response:
        response = super().post(request, *args, **kwargs)
        user = authenticate(username=self.request.data["email"], password=self.request.data["password"])
        login(request, user)
        return response


class UserAPILogout(AuthenticatedView, APIView):
    def post(self: "UserAPILogout", request: Request, **kwargs: dict[str, Any]) -> Response:  # noqa: ARG002
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            return Response(data={"message": "Logged out successfully"}, status=status.HTTP_202_ACCEPTED)
        except TokenError as e:
            return Response(data={"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ActivateAPIUser(APIView):
    def get(self: "ActivateAPIUser", request: Request, uidb64: str, token: str) -> Response:  # noqa: ARG002
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, is_active=False)
        except User.DoesNotExist:
            return Response(
                data={"message": "Invalid activation link or account already activated!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            if account_activation_token.check_token(user, token):
                user.is_active = True
                user.deactivated_at = None
                user.reactivate_until = None
                user.save()
                return Response(
                    data={"message": "Your account has been activated, you can now login!"},
                    status=status.HTTP_202_ACCEPTED,
                )
            return Response(
                data={"message": "Invalid activation link or account already activated!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
