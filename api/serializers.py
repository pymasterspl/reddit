from rest_framework import serializers
from users.models import User 
from core.models import Community, Post

class PostCommentsSerializer():
    pass

class PostSerializer(serializers.ModelSerializer):
    score = serializers.ReadOnlyField()

    class Meta:
        model = Post
        fields = "__all__"


# class PostTopSerializer(PostSerializer):
#     queryset = Post.objects.filter(parent__is=None)


class CommunitySerializer(serializers.ModelSerializer):
    count_online_users = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = "__all__"

    def get_count_online_users(self, obj):
        return obj.count_online_users()
    

class CommunityPostsSerializer(CommunitySerializer):
    # posts = PostSerializer(many=True, read_only=True)
    # posts = PostSerializer(many=True, read_only=True)
    posts = PostSerializer(many=True, queryset=Post.root_posts.all())

class MinimalUserSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("nickname", "avatar", "is_online", "last_activity_ago")

    def get_is_online(self, obj):
        return obj.is_online

    def get_last_activity_ago(self, obj):
        return obj.last_activity_ago

class CommunityMembersSerializer(CommunitySerializer):
    members = MinimalUserSerializer(read_only=True, many=True)