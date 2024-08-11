import pytest
from django.contrib.auth import get_user_model

from core.forms import CommunityForm
from core.models import Community

from .test_utils import generate_random_password

User = get_user_model()


@pytest.mark.django_db()
@pytest.mark.parametrize("data, expected_valid", [
    ({"name": "Test Community", "privacy": "10_PUBLIC"}, True),
    ({"name": "", "privacy": "10_PUBLIC"}, False),
    ({"name": "Test Community", "privacy": "invalid"}, False),
])
def test_community_form(data: dict, expected_valid: bool) -> None:
    user = User.objects.create_user(nickname="testuser", password=generate_random_password(), email="testuser@example.com")
    form = CommunityForm(data=data)
    assert form.is_valid() == expected_valid

    if form.is_valid():
        community = form.save(commit=False)
        community.author = user
        community.save()

        expected_slug = form.cleaned_data["name"].replace(" ", "-").lower()
        assert community.slug == expected_slug
        assert community.name == "Test Community"
        assert community.author == user

        community_from_db = Community.objects.get(name="Test Community")
        assert community_from_db is not None
        assert community_from_db.slug == expected_slug
