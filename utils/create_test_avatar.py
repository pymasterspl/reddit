import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from core.models import User


def create_avatar(user: User) -> None:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp_file:
        image = Image.new("RGB", (100, 100), color=(73, 109, 137))
        image.save(tmp_file, format="JPEG")
        tmp_file.seek(0)

        avatar_file = SimpleUploadedFile(name="test_avatar.jpg", content=tmp_file.read(), content_type="image/jpeg")

        user.avatar = avatar_file
        user.save()

    tmp_file.close()
