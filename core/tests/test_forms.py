import pytest
from django.utils.text import slugify

from core.forms import CommunityForm
from core.models import Community


@pytest.mark.django_db()
def test_community_form():
    form_data = {
        "name": "Test Community",
    }

    form = CommunityForm(data=form_data)

    assert form.is_valid()

    community = form.save(commit=True)

    expected_slug = slugify(form_data["name"])
    assert community.slug == expected_slug

    assert community.name == "Test Community"

    community_from_db = Community.objects.get(name="Test Community")
    assert community_from_db is not None
    assert community_from_db.slug == expected_slug
