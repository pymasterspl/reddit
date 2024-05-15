import hashlib
import re

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
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

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class Post(GenericModel):
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="posts"
    )
    title = models.CharField(max_length=255)
    content = models.TextField()

    tags = GenericRelation(Tag, related_query_name='posts')
    image = models.ImageField(blank=True)
    parent = GenericRelation("self", related_query_name="children")
    version = models.CharField(max_length=32)

    def __str__(self):
        return f"@{self.user}: {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the Post instance first

        hashtags = re.findall(r"#(\w+)", self.content)
        existing_tags = Tag.objects.filter(
            name__in=hashtags,
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id,
        )
        new_tags = [
            Tag(name=hashtag, content_object=self)
            for hashtag in hashtags
            if hashtag not in existing_tags.values_list("name", flat=True)
        ]
        Tag.objects.bulk_create(new_tags)

        self.tags.add(*existing_tags)
        self.tags.add(*new_tags)

        if not self.created_at == self.updated_at:
            self.version = self.generate_version()

    def generate_version(self):
        data = f"{self.title}{self.content}"
        md5_hash = hashlib.md5(data.encode()).hexdigest()

        return md5_hash

    @property
    def up_votes(self):
        return self.post_votes.filter(type=PostVote.UPVOTE).count()

    @property
    def down_votes(self):
        return self.post_votes.filter(type=PostVote.DOWNVOTE).count()

    @property
    def score(self):
        return self.up_votes - self.down_votes


class PostVote(models.Model):
    UPVOTE = "10_UPVOTE"
    DOWNVOTE = "20_DOWNVOTE"
    VOTE_CHOICES = [(UPVOTE, "Up Vote"), (DOWNVOTE, "Down Vote")]

    user = models.ManyToManyField(User, related_name="post_votes")
    post = models.ManyToManyField(Post, related_name="post_votes")
    type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"@{self.user}: {self.type} for post: {self.post}"
