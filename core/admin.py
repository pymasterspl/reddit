from django.contrib import admin

from .models import Community, Image, Post, PostVote, Tag


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at", "updated_at")
    search_fields = ("user__email",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "community", "score", "created_at", "updated_at")
    search_fields = ("title", "user__email", "community__name")
    readonly_fields = ("version",)


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ("choice", "created_at")
    list_filter = ("choice",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("post", "image", "created_at", "updated_at")
