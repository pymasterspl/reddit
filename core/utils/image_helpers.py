from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image

VALID_MIME_TYPES = ["image/jpeg", "image/png", "image/gif"]
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB
REQUIRED_AVATAR_SIZE = 256


def validate_avatar(avatar: ContentFile) -> ContentFile:
    if avatar.content_type not in VALID_MIME_TYPES:
        msg = "Unsupported file type. Use JPEG, PNG, or GIF."
        raise ValidationError(msg)
    if avatar.size > MAX_AVATAR_SIZE:
        msg = "Avatar file size must not exceed 2MB."
        raise ValidationError(msg)

    try:
        img = Image.open(avatar)
        width, height = img.size
    except Exception as err:
        msg = "Invalid image file."
        raise ValidationError(msg) from err

    if width < REQUIRED_AVATAR_SIZE or height < REQUIRED_AVATAR_SIZE:
        msg = "Avatar must be at least 256x256 pixels."
        raise ValidationError(msg)
    if width != height:
        msg = "Avatar must be square."
        raise ValidationError(msg)

    return avatar


def process_image(field_file: ContentFile, max_size: int, quality: int) -> ContentFile:
    img = Image.open(field_file)
    img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return ContentFile(buffer.getvalue(), name=f"{field_file.name.rsplit('.',1)[0]}.jpg")
