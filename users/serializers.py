import typing

from django.db.models import Model
from rest_framework import serializers

from .models import User
from .utils import user_creation


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
        request = self.context.get("request")
        user_creation(user, "api-activate-account", request)
        return user

    def get_message(self: "UserSerializer", obj: User) -> str:
        return f"Account created for {obj}! " f"Please confirm your email to activate " f"your account."
