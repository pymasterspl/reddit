import hashlib
import re
import typing
from datetime import timedelta
from typing import Any, ClassVar

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Case, F, QuerySet, Value, When
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()


class ActiveOnlyManager(models.Manager):
    def get_queryset(self: "ActiveOnlyManager") -> QuerySet:
        return super().get_queryset().filter(is_active=True)


class GenericModel(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    all_objects = models.Manager()
    objects = ActiveOnlyManager()

    class Meta:
        abstract = True


class PostManagerMixin:
    def roots(self: "PostManagerMixin", **kwargs: dict[str, Any]) -> QuerySet["Post"]:
        return self.get_queryset().filter(parent__isnull=True, **kwargs)

    def comments(self: "PostManagerMixin", **kwargs: dict[str, Any]) -> QuerySet["Post"]:
        return self.get_queryset().filter(parent__isnull=False, **kwargs)


class ActivePostManagers(PostManagerMixin, ActiveOnlyManager):
    pass


class PostAwardManager(models.Manager):
    def get_post_awards_anonymous(self: "PostAwardManager") -> QuerySet:
        return (
            self.get_queryset()
            .values(
                "id",
                "post_id",
                "choice",
                "anonymous",
            )
            .annotate(
                giver_anonymous=Case(
                    When(anonymous=True, giver__isnull=False, then=Value("Anonymous")),
                    default=F("giver__nickname"),
                    output_field=models.CharField(max_length=255),
                )
            )
        )


class AllObjectsPostManager(PostManagerMixin, models.Manager):
    pass


class Community(GenericModel):
    PUBLIC: typing.ClassVar[str] = "10_PUBLIC"
    RESTRICTED: typing.ClassVar[str] = "20_RESTRICTED"
    PRIVATE: typing.ClassVar[str] = "30_PRIVATE"

    PRIVACY_CHOICES: typing.ClassVar[list[tuple[str, str]]] = [
        (PUBLIC, "Public - anyone can view and contribute"),
        (RESTRICTED, "Restricted - anyone can view, but only approved users can contribute"),
        (PRIVATE, "Private - only approved users can view and contribute"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="authored_communities")
    members = models.ManyToManyField(User, through="CommunityMember", related_name="communities")
    privacy = models.CharField(max_length=15, choices=PRIVACY_CHOICES, default=RESTRICTED)
    is_18_plus = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Communities"

    def __str__(self: "Community") -> str:
        return str(self.name)

    def save(self: "Community", *args: list, **kwargs: dict) -> None:
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def generate_unique_slug(self: "Community") -> str:
        base_slug = slugify(self.name)
        unique_slug = base_slug
        counter = 1
        while Community.all_objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        return unique_slug

    def count_online_users(self: "Community") -> int:
        online_limit = timezone.now() - timedelta(minutes=settings.LAST_ACTIVITY_ONLINE_LIMIT_MINUTES)
        return self.members.filter(last_activity__gte=online_limit).count()

    def add_moderator(self: "Community", user: User) -> None:
        CommunityService.add_moderator(self, user)

    def remove_moderator(self: "Community", user: User) -> None:
        CommunityService.remove_moderator(self, user)

    def is_admin_or_moderator(self: "Community", user: User) -> bool:
        return (
            CommunityMember.objects.filter(
                community=self, user=user, role__in=[CommunityMember.ADMIN, CommunityMember.MODERATOR]
            ).exists()
            or self.author == user
        )


class CommunityService:
    @staticmethod
    def add_moderator(community: Community, user: User) -> None:
        CommunityMember.objects.update_or_create(
            community=community, user=user, defaults={"role": CommunityMember.MODERATOR}
        )

    @staticmethod
    def remove_moderator(community: Community, user: User) -> None:
        CommunityMember.objects.filter(community=community, user=user, role=CommunityMember.MODERATOR).delete()


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
        related_name="children",
    )
    up_votes = models.IntegerField(default=0)
    down_votes = models.IntegerField(default=0)
    gold = models.IntegerField(default=0)
    version = models.CharField(
        max_length=32,
        help_text="Hash of the title + content to prevent overwriting already saved post",
    )
    display_counter = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    objects = ActivePostManagers()
    all_objects = AllObjectsPostManager()

    def __str__(self: "Post") -> str:
        return f"@{self.author}: {self.title}"

    def save(self: "Post", *args: int, **kwargs: int) -> None:
        if self.pk is not None and self.generate_version() == self.version:
            msg = "The post was already modified"
            raise ValueError(msg)
        self.version = self.generate_version()
        super().save(*args, **kwargs)
        self.update_tags()

    def generate_version(self: "Post") -> str:
        data = f"{self.title}{self.content}{self.is_active}"
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def score(self: "Post") -> int:
        return self.up_votes - self.down_votes

    def get_content_type(self: "Post") -> ContentType:
        return ContentType.objects.get_for_model(self)

    def get_post_awards(self: "Post") -> QuerySet:
        return PostAward.objects.get_post_awards_anonymous().filter(post=self)

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

    def get_images(self: "Post") -> QuerySet:
        return Image.objects.filter(post=self)

    def update_display_counter(self: "Post") -> None:
        Post.objects.filter(pk=self.pk).update(display_counter=F("display_counter") + 1)

    @property
    def children_count(self: "Post") -> int:
        def count_descendants(post: "Post") -> int:
            children = post.children.all()
            total_children = children.count()
            for child in children:
                total_children += count_descendants(child)
            return total_children

        return count_descendants(self)

    def is_top_level(self: "Post") -> bool:
        return self.parent is None

    def is_saved(self: "Post", user: User) -> bool:
        return SavedPost.objects.filter(user=user, post=self).exists()

    def get_comments(self: "Post") -> QuerySet:
        return self.children.all()

    def get_comment_form(self: "Post") -> any:
        from .forms import CommentForm

        return CommentForm(initial={"parent_id": self.pk})


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


class PostAward(models.Model):
    REWARD_POINTS: ClassVar[dict[str, int]] = {
        "1": 15,
        "2": 25,
        "3": 50,
    }

    REWARD_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (f"{level}{i}_REWARD", f"{points} points") for level, points in REWARD_POINTS.items() for i in range(1, 6)
    ]

    giver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="awards_given")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="awards_received")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_awards")
    choice = models.CharField(max_length=20, choices=REWARD_CHOICES, blank=True)  # Placeholder for choices
    gold = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    anonymous = models.BooleanField(default=False)
    comment = models.CharField(max_length=100, blank=True, default="")

    objects = PostAwardManager()

    class Meta:
        unique_together: ClassVar[list[str]] = ["post", "giver"]

    def __str__(self: "PostAward") -> str:
        return f"@{self.giver}: {self.choice} for post: {self.post}"

    def save(self: "PostAward", *args: int, **kwargs: int) -> None:
        self.gold = self.REWARD_POINTS.get(self.choice[0], 0)

        super().save(*args, **kwargs)

        self.post.author.profile.gold_awards = F("gold_awards") + self.gold
        self.post.author.profile.save(update_fields=["gold_awards"])

        Post.objects.filter(pk=self.post.pk).update(gold=F("gold") + self.gold)

    @classmethod
    def get_reward_choices(cls: "PostAward") -> list[tuple[str, str]]:
        return cls.REWARD_CHOICES


class Image(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(default=9999999)

    class Meta:
        ordering: ClassVar[list[str, str]] = ["order", "created_at"]

    def __str__(self: "Image") -> str:
        return f"Image of {self.post}"

    def image_url(self: "Image") -> str:
        try:
            return self.image.url
        except ValueError:
            return ""


class CommunityMember(models.Model):
    MEMBER: ClassVar[str] = "100_member"
    MODERATOR: ClassVar[str] = "200_moderator"
    ADMIN: ClassVar[str] = "300_admin"

    ROLE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (MEMBER, "Member"),
        (MODERATOR, "Moderator"),
        (ADMIN, "Admin"),
    ]

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=13, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("community", "user")

    def __str__(self: "CommunityMember") -> str:
        return f"{self.user.username} - {self.community.name} ({self.role})"


class SavedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_posts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saved_posts")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together: tuple = ("user", "post")
        ordering: ClassVar[list[str]] = ["-saved_at"]

    def __str__(self: "SavedPost") -> str:
        return f"{self.user.username} saved {self.post.title}"

    @staticmethod
    def save_post(user: User, post: Post) -> "SavedPost":
        saved_post, _ = SavedPost.objects.get_or_create(user=user, post=post)
        return saved_post

    @staticmethod
    def remove_saved_post(user: User, post: Post) -> None:
        SavedPost.objects.filter(user=user, post=post).delete()

    @staticmethod
    def get_saved_posts(user: User) -> QuerySet:
        return SavedPost.objects.filter(user=user)


BREAKS_RULES = "10_BREAKS_RULES"
EU_ILLEGAL_CONTENT = "20_EU_ILLEGAL_CONTENT"
HARASSMENT = "30_HARASSMENT"
THREATENING_VIOLENCE = "40_THREATENING_VIOLENCE"
HATE = "50_HATE"
MINOR_ABUSE_OR_SEXUALIZATION = "60_MINOR_ABUSE_OR_SEXUALIZATION"
SHARING_PERSONAL_INFORMATION = "70_SHARING_PERSONAL_INFORMATION"
NON_CONSENSUAL_INTIMATE_MEDIA = "80_NON_CONSENSUAL_INTIMATE_MEDIA"
PROHIBITED_TRANSACTION = "90_PROHIBITED_TRANSACTION"
IMPERSONATION = "100_IMPERSONATION"
COPYRIGHT_VIOLATION = "110_COPYRIGHT_VIOLATION"
TRADEMARK_VIOLATION = "120_TRADEMARK_VIOLATION"
SELF_HARM_OR_SUICIDE = "130_SELF_HARM_OR_SUICIDE"
SPAM = "140_SPAM"
REPORT_CHOICES: list[tuple[str, str]] = [
    (BREAKS_RULES, "Breaks r/fatFIRE rules"),
    (EU_ILLEGAL_CONTENT, "EU illegal content"),
    (HARASSMENT, "Harassment"),
    (THREATENING_VIOLENCE, "Threatening violence"),
    (HATE, "Hate"),
    (MINOR_ABUSE_OR_SEXUALIZATION, "Minor abuse or sexualization"),
    (SHARING_PERSONAL_INFORMATION, "Sharing personal information"),
    (NON_CONSENSUAL_INTIMATE_MEDIA, "Non-consensual intimate media"),
    (PROHIBITED_TRANSACTION, "Prohibited transaction"),
    (IMPERSONATION, "Impersonation"),
    (COPYRIGHT_VIOLATION, "Copyright violation"),
    (TRADEMARK_VIOLATION, "Trademark violation"),
    (SELF_HARM_OR_SUICIDE, "Self-harm or suicide"),
    (SPAM, "Spam"),
]


class PostReport(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=50, choices=REPORT_CHOICES)
    report_details = models.TextField()
    report_person = models.ForeignKey(User, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self: "PostReport") -> str:
        return f"Report for Post {self.post.id} - {self.report_type}"


BAN = "10_BAN"
DELETE = "20_DELETE"
WARN = "30_WARN"
DISMISS_REPORT = "40_DISMISS_REPORT"
ACTION_CHOICES: list[tuple[str, str]] = [
    (BAN, "Ban User"),
    (DELETE, "Delete Post"),
    (WARN, "Warn User"),
    (DISMISS_REPORT, "Dismiss Report"),
]


class AdminAction(models.Model):
    post_report = models.ForeignKey("PostReport", on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self: "AdminAction") -> str:
        return f"{self.get_action_display()} on {self.post_report}"
