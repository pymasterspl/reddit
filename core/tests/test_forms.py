import pytest
from django.contrib.auth import get_user_model

from core.forms import AdminActionForm, CommunityForm, GroupAdminActionForm, PostReportForm
from core.models import BAN, DELETE, DISMISS_REPORT, HATE, WARN, Community, Post

from .test_utils import generate_random_password

User = get_user_model()


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("data", "expected_valid"),
    [
        ({"name": "Test Community", "privacy": "10_PUBLIC"}, True),
        ({"name": "", "privacy": "10_PUBLIC"}, False),
        ({"name": "Test Community", "privacy": "invalid"}, False),
    ],
)
def test_community_form(data: dict, expected_valid: bool) -> None:
    user = User.objects.create_user(
        nickname="testuser", password=generate_random_password(), email="testuser@example.com"
    )
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


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("data", "expected_valid"),
    [
        ({"action_for_selected": BAN}, True),
        ({"action_for_selected": DELETE}, True),
        ({"action_for_selected": ""}, False),
        ({"action_for_selected": "invalid_action"}, False),
    ],
)
def test_group_admin_action_form(data: dict, expected_valid: bool) -> None:
    form = GroupAdminActionForm(data=data)
    assert form.is_valid() == expected_valid


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("data", "expected_valid"),
    [
        ({"report_type": HATE, "report_details": "This post is spam."}, True),
        ({"report_type": HATE, "report_details": "Contains inappropriate content."}, True),
        ({"report_type": "", "report_details": "Some details."}, False),
        ({"report_type": "spam", "report_details": ""}, False),
    ],
)
def test_post_report_form(data: dict, expected_valid: bool) -> None:
    form = PostReportForm(data=data)
    assert form.is_valid() == expected_valid


@pytest.mark.django_db()
def test_post_report_form_save(user: User, post: Post) -> None:
    data = {"report_type": HATE, "report_details": "This post is spam."}
    form = PostReportForm(data=data)
    assert form.is_valid() is True

    post_report = form.save(commit=False)
    post_report.post = post
    post_report.report_person = user
    post_report.save()

    assert post_report.id is not None
    assert post_report.report_type == HATE
    assert post_report.report_details == "This post is spam."


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("data", "expected_valid"),
    [
        ({"action": WARN, "comment": "Looks good."}, True),
        ({"action": DISMISS_REPORT, "comment": ""}, True),
        ({"action": "", "comment": "Some comment"}, False),
        ({"comment": "Missing action"}, False),
        ({"action": "invalid_action", "comment": "Test"}, False),
    ],
)
def test_admin_action_form(data: dict, expected_valid: bool) -> None:
    form = AdminActionForm(data=data)
    assert form.is_valid() == expected_valid
