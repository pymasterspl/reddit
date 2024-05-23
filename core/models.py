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

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return str(self.name)

class Image(models.Model):
    image = models.ImageField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Image of {self.posts}"

    def image_url(self) -> str:
        try:
            return self.image.url
        except ValueError:
            return ""

class Post(GenericModel):
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = GenericRelation(Tag, related_query_name="posts")
    image = models.ManyToManyField(Image, blank=True, related_name="posts")
    parent = models.ForeignKey("self", default=None, blank=True, null=True, on_delete=models.CASCADE, related_query_name="children")
    up_votes = models.IntegerField(default=0)
    down_votes = models.IntegerField(default=0)
    version = models.CharField(
        max_length=32,
        help_text="Hash of the title + content to prevent overwriting already saved post",
    )

    _skip_version_check = False

    def __str__(self) -> str:
        return f"@{self.user}: {self.title}"

    def save(self, *args, **kwargs) -> None:
        if not self._skip_version_check:
            if self.pk is not None and self.generate_version() == self.version:
                raise ValueError("The post was already modified")
            self.version = self.generate_version()
        super().save(*args, **kwargs)
        self.update_tags()

    def generate_version(self) -> str:
        data = f"{self.title}{self.content}"
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def score(self) -> int:
        return self.up_votes - self.down_votes

    def get_content_type(self) -> ContentType:
        return ContentType.objects.get_for_model(self)

    def update_tags(self):
        current_tags = set(re.findall(r"#(\w+)", self.content))
        existing_tags = set(
            Tag.objects.filter(
                content_type=self.get_content_type(),
                object_id=self.id,
            ).values_list("name", flat=True)
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

    def vote(self, user: User, choice: str) -> None:
        vote, _ = PostVote.objects.get_or_create(user=user, post=self)
        vote.choice = choice
        vote.save()


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

    def __str__(self) -> str:
        return f"@{self.user}: {self.choice} for post: {self.post}"

    def save(self: "PostVote", *args: int, **kwargs: int):
        super().save(*args, **kwargs)
        post_vote = PostVote.objects.filter(post=self.post)
        self.post.up_votes = post_vote.filter(choice=PostVote.UPVOTE).count()
        self.post.down_votes = post_vote.filter(choice=PostVote.DOWNVOTE).count()
        self.post._skip_version_check = True
        self.post.save()
        self.post._skip_version_check = False