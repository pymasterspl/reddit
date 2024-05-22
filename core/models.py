import hashlib
import re
from typing import ClassVar

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


class GenericModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    parent = models.ForeignKey()
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Community(GenericModel):
    name = models.CharField(max_length=255)

    def __str__(self: "Community") -> str:
        return str(self.name)


class Tag(models.Model):
    name = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes: ClassVar[list[tuple[str, ...]]] = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self: "Tag") -> str:
        return str(self.name)


class Post(GenericModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()

    tags = GenericRelation(Tag, related_query_name="posts")
    image = models.ManyToManyField(blank=True, related_name="posts")
    parent = GenericRelation("self", related_query_name="children")
    version: str = models.CharField(max_length=32)

    def __str__(self: "Post") -> str:
        return f"@{self.user}: {self.title}"

    def save(self: "Post", *args: int, **kwargs: int) -> None:
        super().save(*args, **kwargs)

        current_tags: set[str] = set(re.findall(r"#(\w+)", self.content))
        existing_tags: set[str] = set(
            Tag.objects.filter(
                content_type=self.get_content_type(),
                object_id=self.id,
            ).values_list("name", flat=True),
        )

        # Remove tags that were removed in the content
        tags_to_remove = existing_tags - current_tags
        Tag.objects.filter(
            name__in=tags_to_remove,
            content_type=self.get_content_type(),
            object_id=self.id,
        ).delete()

        # Add new tags
        new_tags = current_tags - existing_tags
        for tag in new_tags:
            Tag.objects.create(name=tag, content_object=self)

    def generate_version(self: "Post") -> str:
        # Generate hash of title and content to verify if content was overwritten already f.e in other browser
        data = f"{self.title}{self.content}"
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def up_votes(self: "Post") -> int:
        return self.post_votes.filter(type=PostVote.UPVOTE).count()

    @property
    def down_votes(self: "Post") -> int:
        return self.post_votes.filter(type=PostVote.DOWNVOTE).count()

    @property
    def score(self: "Post") -> int:
        return self.up_votes - self.down_votes

    def get_content_type(self: "Post") -> ContentType:
        return ContentType.objects.get_for_model(self)


class PostVote(models.Model):
    UPVOTE = "10_UPVOTE"
    DOWNVOTE = "20_DOWNVOTE"
    VOTE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (UPVOTE, "Up Vote"),
        (DOWNVOTE, "Down Vote"),
    ]

    user = models.ManyToManyField(User, related_name="post_votes")
    post = models.ManyToManyField(Post, related_name="post_votes")
    type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self: "PostVote") -> str:
        return f"@{self.user}: {self.type} for post: {self.post}"


class Image(models.Model):
    image = models.ImageField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self: "Image") -> str:
        return f"Image of {self.posts}"

    def image_url(self: "Image") -> str:
        try:
            return self.image.url()
        except ValueError:
            return ""
