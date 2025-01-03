import datetime
from tokenize import TokenError

import six
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.http import base36_to_int

from users.models import User


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self: "AccountActivationTokenGenerator", user: User, timestamp: int) -> str:
        return six.text_type(user.pk) + six.text_type(timestamp)

    def get_token_lifetime(self: "AccountActivationTokenGenerator", user: User) -> int:
        if user.reactivate_until and user.reactivate_until > timezone.now():
            return int((user.reactivate_until - timezone.now()).total_seconds())
        print(f"settings.PASSWORD_RESET_TIMEOUT: {settings.PASSWORD_RESET_TIMEOUT}")
        return settings.PASSWORD_RESET_TIMEOUT

    def extract_timestamp(self: "AccountActivationTokenGenerator", token: str) -> int:
        try:
            ts_b36 = token.split("-")[0]
            return base36_to_int(ts_b36)
        except (ValueError, IndexError, AttributeError) as e:
            raise TokenError from e

    def check_token(self: "AccountActivationTokenGenerator", user: User, token: str) -> bool:
        if user.reactivate_until is None or user.reactivate_until <= timezone.now():
            return False
        print(f"Reactivate until: {user.reactivate_until}, Now: {timezone.now()}")
        token_timestamp = self.extract_timestamp(token)
        print(f"Token timestamp: {token_timestamp}")
        current_timestamp = int((timezone.now() - datetime.datetime(2001, 1, 1, tzinfo=datetime.UTC)).total_seconds())
        token_lifetime = self.get_token_lifetime(user)
        print(
            f"Current timestamp: {current_timestamp}, Token timestamp: {token_timestamp}, Lifetime: {self.get_token_lifetime(user)}")
        print(f"Result of time subtraction: {current_timestamp - token_timestamp}")
        print(f"Result of token lifetime: {token_lifetime}")

        if (current_timestamp - token_timestamp) > token_lifetime:
            print("Token expired due to lifetime")
            print(f"Result of time subtraction: {current_timestamp - token_timestamp}")
            print(f"Result of token lifetime: {token_lifetime}")
            return False

        return super().check_token(user, token)


account_activation_token = AccountActivationTokenGenerator()
