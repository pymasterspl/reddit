from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations: bool = True

    def _create_user(self: "UserManager", email: str, nickname: str, password: str, **extra_fields: int) -> "User":
        if not email:
            message: str = "Users must have an email address"
            raise ValueError(message)
        if not nickname:
            message: str = "Users must have a nickname"
            raise ValueError(message)
        email = self.normalize_email(email)
        user: User = self.model(email=email, nickname=nickname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self: "UserManager", email: str, nickname: str, password: str, **extra_fields: int) -> "User":
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


class UserSettings(models.Model):

    # https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
    content_lang = models.CharField(
        max_length= 2,
        choices= [
            ("en", "English")
        ]
    )
   #  https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    location = models.CharField(
        max_length=2,
        choices = [
            ("US", "United States")
        ]
    )
    
    is_beta = models.BooleanField(default=False)
    is_over_18 = models.BooleanField(default=False)

    def __str__(self: "UserSettings") -> str:
       return f"{self.user} settings"

class Profile(models.Model):
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
    bio = models.TextField(default="")
    is_nfsw_visible = models.BooleanField(default=False)
    is_followable = models.BooleanField(default=True)
    is_content_visible = models.BooleanField(default=True)
    is_communities_visible = models.BooleanField(default=True)

    def __str__(self: "Profile") -> str:
        return f"{self.nickname} settings"


class User(AbstractUser):
    MALE = "M"
    FEMALE = "F"
    NON_BINARY = "B"
    OTHER = "O"
    NON_SPECIFIED = "N"

    GENDER_CHOICES = {
        MALE: "Male",
        FEMALE: "Female",
        NON_BINARY: "Non-binary",
        OTHER: "Other",
        NON_SPECIFIED: "Non-specified",
    }

    USERNAME_FIELD = "email"
    objects = UserManager()
    username: None = None
    email: str = models.EmailField(unique=True)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    last_activity = models.DateTimeField(auto_now_add=True, db_index=True)
    REQUIRED_FIELDS = ["gender"]
    user_settings = models.OneToOneField(UserSettings, related_name="user", on_delete=models.SET_NULL, null=True)
    profile = models.OneToOneField(Profile, on_delete=models.SET_NULL, null=True)

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
    
    @property
    def nickname(self):
        return self.profile.nickname if self.profile else "not-yet-named"

    @nickname.setter
    def nickname(self, value):
        if self.profile:
            self.profile.nickname = value
            self.profile.save()
            

class SocialLink(models.Model):
    name = models.CharField(max_length=150)
    url = models.URLField()
    user_profile = models.ForeignKey(User, on_delete=models.CASCADE)