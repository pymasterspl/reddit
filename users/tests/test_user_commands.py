import pytest
from django.conf import LazySettings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from freezegun import freeze_time

User = get_user_model()


@freeze_time("2025-01-01 12:00:00")
@pytest.mark.django_db()
def test_anonymize_inactive_users_command(users: list[User], settings: LazySettings) -> None:
    user_to_anonymize = users[0]
    active_user = users[1]

    user_to_anonymize.is_active = False
    user_to_anonymize.deactivated_at = timezone.now() - timezone.timedelta(
        days=settings.ACCOUNT_EXPIRATION_TIME_IN_DAYS
    )
    user_to_anonymize.reactivate_until = timezone.now() - timezone.timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
    user_to_anonymize.save()

    call_command("anonymize_inactive_users")
    user_to_anonymize.refresh_from_db()
    active_user.refresh_from_db()
    assert user_to_anonymize.is_active is False
    assert user_to_anonymize.anonymized_at
    assert user_to_anonymize.nickname.startswith("deleted_user_")
    assert active_user.is_active
    assert active_user.nickname.startswith("test_user_")


@freeze_time("2025-01-01 12:00:00")
@pytest.mark.django_db()
def test_anonymize_inactive_users_command_cannot_anonymize_user_with_valid_reactivate_date(
    users: list[User], settings: LazySettings
) -> None:
    active_user = users[0]
    inactive_user = users[1]
    reactivate_until = timezone.now() - timezone.timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT - 1)
    inactive_user.deactivated_at = timezone.now() - timezone.timedelta(days=settings.ACCOUNT_EXPIRATION_TIME_IN_DAYS)
    inactive_user.reactivate_until = reactivate_until
    active_user.reactivate_until = reactivate_until
    inactive_user.is_active = False
    inactive_user.save()
    active_user.save()
    call_command("anonymize_inactive_users")
    inactive_user.refresh_from_db()
    active_user.refresh_from_db()
    assert not inactive_user.is_active
    assert active_user.is_active
    assert not inactive_user.anonymized_at
    assert not active_user.anonymized_at
    assert inactive_user.reactivate_until == reactivate_until
    assert active_user.reactivate_until == reactivate_until
