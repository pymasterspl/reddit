from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image

from reddit import settings


def _validate_image_file(image_file: Image, max_size_mb: int) -> None:
    try:
        img = Image.open(image_file)
        img.verify()
    except (OSError, SyntaxError) as err:
        raise ValidationError(_("Uploaded file is not a valid image.")) from err

    img = Image.open(image_file)

    allowed_formats = ["JPEG", "PNG", "JPG"]
    if img.format not in allowed_formats:
        raise ValidationError(_("Only JPEG and PNG image formats are supported."))

    max_width, max_height = 1920, 1080
    width, height = img.size
    if width > max_width or height > max_height:
        raise ValidationError(_("Image is too large. Maximum resolution is %sx%s pixels.") % (max_width, max_height))
    max_file_size = max_size_mb * 1024 * 1024
    if image_file.size > max_file_size:
        raise ValidationError(_("File size must not exceed %.2f MB.") % max_size_mb)


def validate_avatar_file(image_file: Image) -> None:
    _validate_image_file(image_file, max_size_mb=settings.MAX_AVATAR_SIZE_MB)


def validate_banner_file(image_file: Image) -> None:
    max_size_kb = settings.MAX_BANNER_SIZE_KB
    _validate_image_file(image_file, max_size_mb=max_size_kb / 1024)
