from typing import Any, ClassVar

from django.contrib.auth import authenticate, login, logout
from requests import Request
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import UserSerializer


class UserAPIRegistration(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserAPILogin(TokenObtainPairView):
    def post(self: "UserAPILogin", request: Request, *args: tuple, **kwargs: dict[str, Any]) -> Response:
        response = super().post(request, *args, **kwargs)
        user = authenticate(username=self.request.data["email"], password=self.request.data["password"])
        login(request, user)
        return response


class UserAPILogout(TokenRefreshView):
    permission_classes: ClassVar[list] = [IsAuthenticated]
    authentication_classes: ClassVar[list] = [JWTStatelessUserAuthentication]

    def post(self: "UserAPILogout", request: Request, **kwargs: dict[str, Any]) -> Response:  # noqa: ARG002
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            return Response(data={"message": "Logged out successfully"}, status=status.HTTP_202_ACCEPTED)
        except TokenError as e:
            return Response(data={"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
