from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from reddit.settings import MAX_AVATAR_SIZE_MB
from users.validators import _validate_image_file


def create_test_image(
    image_format: str = "JPEG",
    size: tuple[int, int] = (100, 100),
    color: tuple[int, int, int] = (255, 0, 0),
    oversized: bool = False,
) -> SimpleUploadedFile:
    img = Image.new("RGB", size, color)
    image_io = BytesIO()
    img.save(image_io, format=image_format)
    image_io.seek(0)

    image_content = image_io.getvalue() + b"a" * (2 * 1024 * 1024) if oversized else image_io.getvalue()

    return SimpleUploadedFile("test_image.jpg", image_content, content_type=f"image/{image_format.lower()}")


@pytest.mark.parametrize("image_format", ["JPEG", "PNG"])
def test_valid_image_formats(image_format: str) -> None:
    image_file = create_test_image(image_format=image_format)
    try:
        _validate_image_file(image_file, MAX_AVATAR_SIZE_MB)
    except ValidationError:
        pytest.fail(f"Validation failed for valid {image_format} image.")


def test_invalid_image_format() -> None:
    invalid_file = SimpleUploadedFile("not_an_image.txt", b"not-a-real-image", content_type="text/plain")
    with pytest.raises(ValidationError, match="Uploaded file is not a valid image."):
        _validate_image_file(invalid_file, MAX_AVATAR_SIZE_MB)


def test_image_with_unsupported_format() -> None:
    image_file = create_test_image(image_format="BMP")
    with pytest.raises(ValidationError, match="Only JPEG and PNG image formats are supported."):
        _validate_image_file(image_file, MAX_AVATAR_SIZE_MB)


def test_image_too_large_dimensions() -> None:
    max_width, max_height = 1920, 1080
    image_file = create_test_image(size=(max_width + 1, max_height + 1))
    with pytest.raises(ValidationError) as excinfo:
        _validate_image_file(image_file, 5)
    assert "Image is too large. Maximum resolution is 1920x1080 pixels." in excinfo.value.messages[0]


def test_valid_image_dimensions() -> None:
    max_width, max_height = 1920, 1080
    image_file = create_test_image(size=(max_width, max_height))
    try:
        _validate_image_file(image_file, MAX_AVATAR_SIZE_MB)
    except ValidationError:
        pytest.fail("Validation failed for an image within valid dimensions.")


def test_image_exceeding_file_size() -> None:
    oversized_image_file = create_test_image(oversized=True)
    with pytest.raises(ValidationError, match="File size must not exceed"):
        _validate_image_file(oversized_image_file, MAX_AVATAR_SIZE_MB)


def test_corrupted_image_file() -> None:
    image_file = create_test_image()
    corrupted_image_file = SimpleUploadedFile("corrupted.jpg", image_file.read()[:10], content_type="image/jpeg")
    with pytest.raises(ValidationError, match="Uploaded file is not a valid image."):
        _validate_image_file(corrupted_image_file, MAX_AVATAR_SIZE_MB)
