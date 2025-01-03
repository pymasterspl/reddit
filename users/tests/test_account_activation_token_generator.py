import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from tokenize import TokenError

from ..tokens import AccountActivationTokenGenerator
from unittest.mock import patch
User = get_user_model()


@pytest.fixture
def token_generator():
    return AccountActivationTokenGenerator()
@pytest.mark.django_db()
def test_make_hash_value(token_generator: AccountActivationTokenGenerator, user: User) -> None:
    timestamp = 123456
    result = token_generator._make_hash_value(user, timestamp)
    expected = str(user.pk) + str(timestamp)
    assert result == expected

@pytest.mark.django_db()
def test_get_token_lifetime_default(token_generator: AccountActivationTokenGenerator, user: User, settings) -> None:
    settings.PASSWORD_RESET_TIMEOUT = 3600
    result = token_generator.get_token_lifetime(user)
    assert result == 3600

@pytest.mark.django_db()
def test_get_token_lifetime_with_reactivate_until(token_generator: AccountActivationTokenGenerator, user: User) -> None:
    mock_now = timezone.now()
    user.reactivate_until = mock_now + timezone.timedelta(seconds=7200)
    user.save()
    user.refresh_from_db()
    with patch("django.utils.timezone.now", return_value=mock_now):
        assert token_generator.get_token_lifetime(user) == 7200

@pytest.mark.django_db()
def test_extract_timestamp_valid(token_generator: AccountActivationTokenGenerator) -> None:
    token = "2n9c-abcdef" # base36_to_int(2n9c) => 123456
    assert token_generator.extract_timestamp(token=token) == 123456

@pytest.mark.django_db()
def test_extract_timestamp_invalid_format(token_generator: AccountActivationTokenGenerator) -> None:
    with pytest.raises(TokenError):
        token_generator.extract_timestamp(token="-abcdef")
    with pytest.raises(TokenError):
        token_generator.extract_timestamp(token=None)
    with pytest.raises(TokenError):
        token_generator.extract_timestamp(token="]-abcdef")

@pytest.mark.django_db()
def test_check_token_expired_reactivate_until(token_generator: AccountActivationTokenGenerator, user: User) -> None:
    user.reactivate_until = timezone.now() - timezone.timedelta(hours=1)
    user.save()
    user.refresh_from_db()
    token = token_generator.make_token(user)
    assert not token_generator.check_token(user, token=token)

@pytest.mark.django_db()
def test_check_token_expired_reactivate_until_is_none(token_generator: AccountActivationTokenGenerator, user: User) -> None:
    token = token_generator.make_token(user)
    assert not token_generator.check_token(user, token=token)

@pytest.mark.django_db()
def test_check_token_valid(token_generator: AccountActivationTokenGenerator, inactive_user: User) -> None:
    user = inactive_user
    user.reactivate_until = timezone.now() + timezone.timedelta(hours=1)
    user.save()
    user.refresh_from_db()
    token = token_generator.make_token(user)
    assert token_generator.check_token(user, token=token)
