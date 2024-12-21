import io
from datetime import timedelta
from pathlib import Path
from typing import ClassVar

from django.apps import apps
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image

from .choices import GENDER_CHOICES, get_languages, get_locations
from reddit.settings import TIME_EXPIRATION_IN_DAYS
from .validators import validate_avatar_file, validate_banner_file

from reddit.settings import ACCOUNT_EXPIRATION_TIME_IN_DAYS


def user_avatar_path(_: Model, filename: str) -> Path:
    return Path("users_avatars") / filename


def user_banner_path(_: Model, filename: str) -> Path:
    return Path("users_banners") / filename


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
        user.save()
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


class UserSettings(models.Model):
    content_lang = models.CharField(max_length=2, choices=get_languages, default="en")
    user = models.OneToOneField("User", on_delete=models.CASCADE, null=False)  # default name usersettings
    location = models.CharField(max_length=2, choices=get_locations, default="PL")

    is_beta = models.BooleanField(default=False)
    revert_to_old_reddit = models.BooleanField(default=False)
    is_over_18 = models.BooleanField(default=False)

    def __str__(self: "UserSettings") -> str:
        return f"{self.user}"


class Profile(models.Model):
    bio = models.TextField(default="", max_length=1000)
    is_nsfw = models.BooleanField(
        default=False,
        help_text=(
            "Profile contains content which is NSFW "
            "(may contain nudity, pornography, profanity, or inappropriate content for those under 18)"
        ),
    )
    is_followable = models.BooleanField(default=True)
    is_content_visible = models.BooleanField(default=True)
    is_communities_visible = models.BooleanField(default=True)
    comment_karma = models.IntegerField(default=0)
    post_karma = models.IntegerField(default=0)
    gold_awards = models.IntegerField(default=0)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True,
        default=None,
        validators=[
            FileExtensionValidator(allowed_extensions=list(settings.WHITELISTED_IMAGE_TYPES.keys())),
            validate_avatar_file,
        ],
    )
    banner = models.ImageField(
        upload_to=user_banner_path,
        null=True,
        blank=True,
        default=None,
        validators=[
            FileExtensionValidator(allowed_extensions=list(settings.WHITELISTED_IMAGE_TYPES.keys())),
            validate_banner_file,
        ],
    )
    user = models.OneToOneField("User", on_delete=models.CASCADE, null=False)

    def __str__(self: "Profile") -> str:
        return f"{self.user.nickname}"

    def save(self: "Profile", *args: any, **kwargs: dict) -> None:
        if self.avatar != self._initial_avatar:
            self.avatar = self.process_image(self.avatar, (32, 32))
        if self.banner != self._initial_banner:
            self.banner = self.process_image(self.banner, (300, 100))
        super().save(*args, **kwargs)

    def __init__(self: "Profile", *args: any, **kwargs: any) -> None:
        super().__init__(*args, **kwargs)
        self._initial_avatar = self.__dict__.get("avatar")
        self._initial_banner = self.__dict__.get("banner")


    def nickname(self: "Profile") -> str:
        return self.user.nickname

    def email(self: "Profile") -> str:
        return self.user.email

    @staticmethod
    def process_image(image_file: any, size: tuple[int, int], formatting: str = "JPEG") -> ContentFile:
        image = Image.open(image_file)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image = image.resize(size, Image.LANCZOS)
        image_io = io.BytesIO()
        image.save(image_io, format=formatting)
        return ContentFile(image_io.getvalue(), image_file.name)

    @property
    def avatar_url(self: "Profile") -> str:
        if self.avatar and hasattr(self.avatar, "url"):
            try:
                return self.avatar.url
            except ValueError:
                return settings.DEFAULT_AVATAR_URL
        return settings.DEFAULT_AVATAR_URL

    @property
    def banner_url(self: "Profile") -> str:
        if self.banner and hasattr(self.banner, "url"):
            try:
                return self.banner.url
            except ValueError:
                return settings.DEFAULT_BANNER_URL
        return settings.DEFAULT_BANNER_URL

    def delete_avatar(self: "Profile") -> None:
        if self.avatar:
            if default_storage.exists(self.avatar.path):
                default_storage.delete(self.avatar.path)
            self.avatar = None
            self.save()

    def delete_banner(self: "Profile") -> None:
        if self.banner:
            if default_storage.exists(self.banner.path):
                default_storage.delete(self.banner.path)
            self.banner = settings.DEFAULT_BANNER_URL
            self.save()


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

    objects = UserManager()
    username: None = None
    email = models.EmailField(unique=True)
    last_activity = models.DateTimeField(auto_now_add=True, db_index=True)
    can_create_post = models.BooleanField(
        default=True, help_text="Indicates whether the user can create posts. Defaults to True."
    )
    warnings = models.IntegerField(default=0, help_text="The number of warnings assigned to the user. Defaults to 0.")
    deactivated_at = models.DateTimeField(null=True, blank=True)
    reactivate_until = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["nickname"]

    def has_permission(self: "User", post_id: int, permission_name: str) -> bool:
        permission_checkers = {
            "edit": self.__check_permission_post_edit,
            # Add more permissions here if needed
        }
        checker = permission_checkers.get(permission_name)
        if checker:
            return checker(post_id)
        return False

    def __check_permission_post_edit(self: "User", post_id: int) -> bool:
        Post = apps.get_model("core", "Post")
        CommunityMember = apps.get_model("core", "CommunityMember")

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return False

        if self == post.author:
            return True

        try:
            community_member = CommunityMember.objects.get(community=post.community, user=self)
        except CommunityMember.DoesNotExist:
            return False

        return community_member.role in {
            CommunityMember.MODERATOR,
            CommunityMember.ADMIN,
        }

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

    def deactivate(self) -> None:
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.reactivate_until = timezone.now() + timedelta(days=ACCOUNT_EXPIRATION_TIME_IN_DAYS)
        self.save()

    def anonymize_account(self) -> None:
        if not self.is_active and self.reactivate_until and self.reactivate_until <= timezone.now():
            with transaction.atomic():
                self.is_active = False
                self.nickname = f"deleted_user_{self.pk}"
                self.email = f"deleted_user_{self.pk}@example.com"
                self.password = ""
                self.first_name = ""
                self.last_name = ""
                self.is_staff = False
                self.is_superuser = False
                self.can_create_post = False
                self.reactivate_until = None
                self.anonymize_related_models()
                self.save()

    def anonymize_related_models(self) -> None:
        try:
            self.usersettings.delete()
        except UserSettings.DoesNotExist:
            pass
        try:
            profile = self.profile
        except Profile.DoesNotExist:
            pass
        else:
            profile.bio = ""
            profile.is_nsfw = False
            profile.is_followable = False
            profile.is_content_visible = False
            profile.is_communities_visible = False
            profile.gender = ""
            profile.user = self
            profile.delete_avatar()
            profile.delete_banner()
            profile.save()
        SocialLink.objects.filter(profile__user=self).delete()

class SocialLink(models.Model):
    name = models.CharField(max_length=150)
    url = models.URLField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=False, related_name="sociallink")

    def __str__(self: "SocialLink") -> str:
        return f"Social link: {self.url}"
