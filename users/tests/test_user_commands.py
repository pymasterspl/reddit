import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db()
def test_anonymize_inactive_users_command(user: User, inactive_user: User) -> None:
    user_to_anonymize = inactive_user
    active_user = user
    call_command("anonymize_inactive_users")
    user_to_anonymize.refresh_from_db()
    active_user.refresh_from_db()
    assert user_to_anonymize.is_active is False
    assert user_to_anonymize.reactivate_until is None
    assert user_to_anonymize.nickname.startswith("deleted_user_")
    assert active_user.is_active is True
    assert active_user.nickname == "test_user"


@pytest.mark.django_db()
def test_anonymize_inactive_users_command_cannot_anonymize_user_with_future_reactivate_date(
    user: User, inactive_user: User
) -> None:
    active_user = user
    reactivate_until = timezone.now() + timezone.timedelta(days=1)
    inactive_user.reactivate_until = reactivate_until
    active_user.reactivate_until = reactivate_until
    inactive_user.save()
    active_user.save()
    call_command("anonymize_inactive_users")
    inactive_user.refresh_from_db()
    active_user.refresh_from_db()
    assert inactive_user.is_active is False
    assert active_user.is_active is True
    assert inactive_user.reactivate_until == reactivate_until
    assert active_user.reactivate_until == reactivate_until
