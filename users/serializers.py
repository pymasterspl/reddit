import typing

from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import Model
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers

from reddit import settings

from .models import User
from .tokens import account_activation_token


class UserSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model: Model = User
        fields: typing.ClassVar[list] = ["nickname", "email", "password", "password2", "message"]

    def validate(self: "UserSerializer", attrs: dict) -> dict:
        if attrs["password"] != attrs["password2"]:
            msg = {"password": "Passwords are not the same", "password2": "Passwords are not the same"}
            raise serializers.ValidationError(msg)
        return attrs

    def create(self: "UserSerializer", validated_data: dict) -> User:
        user = User.objects.create(nickname=validated_data["nickname"], email=validated_data["email"], is_active=False)
        user.set_password(validated_data["password"])
        user.save()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        request = self.context.get("request")
        protocol = "https" if request.is_secure() else "http"
        current_site = get_current_site(request)
        activation_link = reverse("activate-account", kwargs={"uidb64": uid, "token": token})
        full_activation_link = f"{protocol}://{current_site.domain}{activation_link}"
        send_mail(
            "Confirm your registration",
            f"Please click on the following link to confirm your registration " f"{activation_link}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
            html_message=render_to_string(
                "users/account_activation_email.html",
                {
                    "user": user,
                    "activation_link": full_activation_link,
                },
            ),
        )
        return user

    def get_message(self: "UserSerializer", obj: User) -> str:
        return f"Account created for {obj}! " f"Please confirm your email to activate " f"your account."
