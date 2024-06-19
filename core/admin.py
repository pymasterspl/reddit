from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from .models import Community, Image, Post, PostVote, Tag


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "created_at", "updated_at")
    search_fields = ("author__email",)

    def get_queryset(self: "Community", _request: HttpRequest) -> models.QuerySet:
        return Community.all_objects.all()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "score", "display_counter", "author", "created_at", "updated_at")
    search_fields = ("title", "author__email", "community__name")
    readonly_fields = ("version", "display_counter", "up_votes", "down_votes")

    def get_queryset(self: "PostAdmin", _request: HttpRequest) -> models.QuerySet:
        return Post.all_objects.all()


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
