import pytest
from django.contrib.auth import get_user_model

from core.forms import CommunityForm
from core.models import Community

from .test_utils import generate_random_password

User = get_user_model()


@pytest.mark.django_db()
def test_community_form() -> None:
    user_password = generate_random_password()
    user = User.objects.create_user(email="test@example.com", password=user_password, nickname="testnick")
    form_data = {
        "name": "Test Community",
        "privacy": "PUBLIC",
        "is_18_plus": True,
    }

    form = CommunityForm(data=form_data)
    assert form.is_valid()

    community = form.save(commit=False)
    community.author = user
    community.save()

    expected_slug = form.cleaned_data["name"].replace(" ", "-").lower()
    assert community.slug == expected_slug
    assert community.name == "Test Community"
    assert community.is_18_plus is True
    assert community.author == user

    community_from_db = Community.objects.get(name="Test Community")
    assert community_from_db is not None
    assert community_from_db.slug == expected_slug
