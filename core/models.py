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
        indexes: ClassVar[list[models.Index]] = [
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
    parent = models.ForeignKey(
        "self",
        default=None,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_query_name="children",
    )
    up_votes = models.IntegerField(default=0)
    down_votes = models.IntegerField(default=0)
    version = models.CharField(
        max_length=32,
        help_text="Hash of the title + content to prevent overwriting already saved post",
    )

    def __str__(self: "Post") -> str:
        return f"@{self.user}: {self.title}"

    def save(self: "Post", *args: int, **kwargs: int) -> None:
        if self.pk is not None and self.generate_version() == self.version:
            msg = "The post was already modified"
            raise ValueError(msg)
        self.version = self.generate_version()
        super().save(*args, **kwargs)
        self.update_tags()

    def generate_version(self: "Post") -> str:
        data = f"{self.title}{self.content}"
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def score(self: "Post") -> int:
        return self.up_votes - self.down_votes

    def get_content_type(self: "Post") -> ContentType:
        return ContentType.objects.get_for_model(self)

    def update_tags(self: "Post") -> None:
        current_tags = set(re.findall(r"#(\w+)", self.content))
        existing_tags = set(
            Tag.objects.filter(
                content_type=self.get_content_type(),
                object_id=self.id,
            ).values_list("name", flat=True),
        )
        tags_to_remove = existing_tags - current_tags
        Tag.objects.filter(
            name__in=tags_to_remove,
            content_type=self.get_content_type(),
            object_id=self.id,
        ).delete()
        new_tags = current_tags - existing_tags
        for tag in new_tags:
            Tag.objects.create(name=tag, content_object=self)

    def vote(self: "Post", user: User, choice: str) -> None:
        vote, _ = PostVote.objects.get_or_create(user=user, post=self)
        vote.choice = choice
        vote.save()

    def get_images(self: "Post") -> models.QuerySet:
        return Image.objects.filter(post=self)


class PostVote(models.Model):
    UPVOTE = "10_UPVOTE"
    DOWNVOTE = "20_DOWNVOTE"
    VOTE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (UPVOTE, "Up Vote"),
        (DOWNVOTE, "Down Vote"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_votes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_votes")
    choice = models.CharField(max_length=20, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together: ClassVar[list[str]] = ["post", "user"]

    def __str__(self: "PostVote") -> str:
        return f"@{self.user}: {self.choice} for post: {self.post}"

    def save(self: "PostVote", *args: int, **kwargs: int) -> None:
        super().save(*args, **kwargs)
        post_votes = PostVote.objects.filter(post=self.post)
        up_votes = post_votes.filter(choice=PostVote.UPVOTE).count()
        down_votes = post_votes.filter(choice=PostVote.DOWNVOTE).count()
        Post.objects.filter(pk=self.post.pk).update(up_votes=up_votes, down_votes=down_votes)


class Image(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=9999999)

    class Meta:
        ordering: ClassVar[list[str, str]] = ["order", "created_at"]

    def __str__(self: "Image") -> str:
        return f"Image of {self.posts}"

    def image_url(self: "Image") -> str:
        try:
            return self.image.url
        except ValueError:
            return ""