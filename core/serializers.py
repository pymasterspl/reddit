from rest_framework import serializers
from users.models import User 
from core.models import Community, Post

class PostCommentsSerializer():
    pass

class PostSerializer(serializers.ModelSerializer):
    score = serializers.ReadOnlyField()

    class Meta:
        model = Post
        exclude = ["version"]

class CommunitySerializer(serializers.ModelSerializer):
    count_online_users = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = "__all__"

    def get_count_online_users(self, obj):
        return obj.count_online_users()
    

class MinimalCommunitySerializer(CommunitySerializer):
    class Meta(CommunitySerializer.Meta):
        fields = ("id", "name", "slug")


class MinimalUserSerializer(serializers.ModelSerializer):
    is_online = serializers.ReadOnlyField()
    last_activity_ago = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ("nickname", "avatar", "is_online", "last_activity_ago")


class CommunityMembersSerializer(CommunitySerializer):
    members = MinimalUserSerializer(read_only=True, many=True)


class CommunityPostsSerializer(CommunitySerializer):
    posts = PostSerializer(many=True, read_only=True)