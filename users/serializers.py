from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.ReadOnlyField()
    last_activity_ago = serializers.ReadOnlyField()
    class Meta:
        model = get_user_model()
        fields = ["nickname", "email", "avatar", "profile", "usersettings", "is_online", "last_activity_ago", "last_activity"]