import io
from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image
from core.models import Post, CommunityMember


class UserManager(BaseUserManager):
    use_in_migrations: bool = True

    def _create_user(self: "UserManager", email: str, nickname: str, password: str, **extra_fields: dict) -> "User":
        if not email:
            message: str = "Users must have an email address"
            raise ValueError(message)
        if not nickname:
            message: str = "Users must have a nickname"
            raise ValueError(message)
        email = self.normalize_email(email)
        user = self.model(email=email, nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self: "UserManager", email: str, nickname: str, password: str, **extra_fields: dict) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(email, nickname, password, **extra_fields)

    def create_superuser(self: "UserManager", email: str, nickname: str, password: str, **extra_fields: dict) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            message: str = "Superuser must have is_staff=True."
            raise ValueError(message)
        if extra_fields.get("is_superuser") is not True:
            message: str = "Superuser must have is_superuser=True."
            raise ValueError(message)

        return self._create_user(email, nickname, password, **extra_fields)


class User(AbstractUser):
    nickname_validator = UnicodeUsernameValidator()

    nickname = models.CharField(
        max_length=150,
        null=False,
        blank=False,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        ),
        validators=[nickname_validator],
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["nickname"]
    objects = UserManager()
    username: None = None
    email = models.EmailField(unique=True)
    last_activity = models.DateTimeField(auto_now_add=True, db_index=True)
    avatar = models.ImageField(upload_to="users_avatars/", null=True, blank=True, default=None)

    def __str__(self: "User") -> str:
        return self.nickname

    def save(self: "User", *args: any, **kwargs: dict) -> None:
        if self.avatar:
            self.avatar = self.process_avatar(self.avatar)
        super().save(*args, **kwargs)

    def has_permission(self, post_id: int, permission_name: str) -> bool:
        post = Post.objects.get(id=post_id)
        match permission_name:
            case "edit":
                if self.user == post.author:
                    return True

                community_member = CommunityMember.objects.filter(
                    community=post.community,
                    user=self.user
                ).first()

                if community_member and community_member.role in [CommunityMember.MODERATOR, CommunityMember.ADMIN]:
                    return True
            case _:
                return False

    def process_avatar(self: "User", avatar: any) -> ContentFile:
        image = Image.open(avatar)
        image = image.resize((32, 32), Image.LANCZOS)
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        return ContentFile(image_io.getvalue(), avatar.name)

    def get_avatar_url(self: "User") -> str:
        if self.avatar:
            return self.avatar.url
        return "/static/images/avatars/default_avatar.jpg"

    def update_last_activity(self: "User") -> None:
        User.objects.filter(pk=self.pk).update(last_activity=timezone.now())

    @property
    def is_online(self: "User") -> bool:
        online_limit = timezone.now() - timedelta(minutes=settings.LAST_ACTIVITY_ONLINE_LIMIT_MINUTES)
        return self.last_activity >= online_limit

    @property
    def last_activity_ago(self: "User") -> str:
        delta = timezone.now() - self.last_activity

        if delta.days == 0:
            if delta.seconds < 60:  # noqa: PLR2004
                return "just now"
            if delta.seconds < 3600:  # noqa: PLR2004
                return f"{delta.seconds // 60} minutes ago"
            return f"{delta.seconds // 3600} hours ago"
        if delta.days == 1:
            return "1 day ago"
        return f"{delta.days} days ago"
