from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator


class UserManager(BaseUserManager):
    use_in_migrations: bool = True

    def _create_user(self: "UserManager", email: str, nickname:str, password: str, **extra_fields: int) -> "User":
        if not email:
            message: str = "Users must have an email address"
            raise ValueError(message)
        if not nickname:
            message: str = "Users must have a nickname"
            raise ValueError(message)
        email = self.normalize_email(email)
        user: User = self.model(email=email, nickname=nickname, password=password, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self: "UserManager", email: str, nickname:str, password: str, **extra_fields: int) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        
        return self._create_user(email, nickname, password, **extra_fields)

    def create_superuser(self: "UserManager", email: str, nickname: str, password: str, **extra_fields: int) -> "User":

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
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[nickname_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[int]] = ["nickname"],
    objects = UserManager()
    username: None = None
    email: str = models.EmailField(unique=True)
    last_activity = models.DateTimeField(auto_now_add=True, db_index=True)

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
                result = "just now"
            elif delta.seconds < 3600:  # noqa: PLR2004
                result = f"{delta.seconds // 60} minutes ago"
            else:
                result = f"{delta.seconds // 3600} hours ago"
        elif delta.days == 1:
            result = "1 day ago"
        else:
            result = f"{delta.days} days ago"

        return result
