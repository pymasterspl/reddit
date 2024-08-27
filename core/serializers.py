from collections.abc import Sequence
from typing import ClassVar

from django.db.models import Model
from rest_framework import serializers

from core.models import Community, Post
from users.models import User


class PostSerializer(serializers.ModelSerializer):
    score = serializers.ReadOnlyField()

    class Meta:
        model: Model = Post
        exclude: ClassVar[Sequence[str] | str] = ["version"]


class CommunitySerializer(serializers.ModelSerializer):
    count_online_users = serializers.SerializerMethodField()

    class Meta:
        model: Model = Community
        fields: ClassVar[Sequence[str] | str] = "__all__"

    def get_count_online_users(self: "CommunitySerializer", obj: Community) -> int:
        return obj.count_online_users()


class MinimalCommunitySerializer(CommunitySerializer):
    class Meta(CommunitySerializer.Meta):
        fields: ClassVar[Sequence[str] | str] = ("id", "name", "slug")


class MinimalUserSerializer(serializers.ModelSerializer):
    is_online = serializers.ReadOnlyField()
    last_activity_ago = serializers.ReadOnlyField()

    class Meta:
        model: Model = User
        fields: ClassVar[Sequence[str] | str] = ("nickname", "avatar", "is_online", "last_activity_ago")


class CommunityMembersSerializer(CommunitySerializer):
    members = MinimalUserSerializer(read_only=True, many=True)


class CommunityPostsSerializer(CommunitySerializer):
    posts = PostSerializer(many=True, read_only=True)
