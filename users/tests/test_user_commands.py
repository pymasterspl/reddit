import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

User = get_user_model()

@pytest.mark.django_db()
def test_anonymize_inactive_users_command(generated_password: str) -> None:
    user_to_anonymize = User.objects.create(
        nickname="test_user",
        email="test_user@example.com",
        password=generated_password,
        is_active=False,
        deactivated_at=timezone.now(),
        reactivate_until=timezone.now(),
    )
    active_user = User.objects.create(
        nickname="active_user",
        email="active_user@example.com",
        password=generated_password,
        is_active=True,
    )
    call_command("anonymize_inactive_users")
    user_to_anonymize.refresh_from_db()
    active_user.refresh_from_db()
    assert user_to_anonymize.is_active is False
    assert user_to_anonymize.reactivate_until is None
    assert user_to_anonymize.nickname.startswith("deleted_user_")
    assert active_user.is_active is True
    assert active_user.nickname == "active_user"