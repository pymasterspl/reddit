from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models import Profile, UserSettings


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "nickname", "email", "avatar", "profile", "usersettings", 
            "is_online", "last_activity_ago", "last_activity"
        ]
        read_only_fields = ["profile", "usersettings", "is_online", "last_activity_ago", "last_activity"]
        # That leaves nickname, email, avatar 
                            
class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="user.avatar", allow_null=True, required=False)
    nickname = serializers.CharField(source="user.nickname", allow_blank=False)
    class Meta:
        model = Profile
        fields = [
            "id", "nickname", "gender", "bio", "avatar",
            "post_karma", "comment_karma", "is_nsfw",
            "is_followable", "is_content_visible",
            "is_communities_visible"
        ]
        read_only_fields = ["post_karma", "comment_karma"]


    def update(self, instance, validated_data):
        # Update the related User model fields
        user = instance.user
        user.avatar = validated_data.get('avatar', user.avatar)
        user.nickname = validated_data.get('nickname', user.nickname)
        user.save()

        # Update the Profile fields
        instance.bio = validated_data.get('bio', instance.bio)
        instance.is_nsfw = validated_data.get('is_nsfw', instance.is_nsfw)
        instance.is_followable = validated_data.get('is_followable', instance.is_followable)
        instance.is_content_visible = validated_data.get('is_content_visible', instance.is_content_visible)
        instance.is_communities_visible = validated_data.get('is_communities_visible', instance.is_communities_visible)
        # Exclude instance.comment_karma - read_only
        # Exclude instance.post_karma - read_only
        instance.gender = validated_data.get('gender', instance.gender)

        instance.save()
        return instance
    

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ["user", "location", "content_lang", "is_beta", "is_over_18"]
        read_only_fields = ["user"]