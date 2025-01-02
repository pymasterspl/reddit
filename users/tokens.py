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
        return settings.PASSWORD_RESET_TIMEOUT

    def extract_timestamp(self: "AccountActivationTokenGenerator", token: str) -> int:
        try:
            ts_b36 = token.split("-")[0]
            return base36_to_int(ts_b36)
        except (ValueError, IndexError) as e:
            raise TokenError from e

    def check_token(self: "AccountActivationTokenGenerator", user: User, token: str) -> bool:
        try:
            token_timestamp = self.extract_timestamp(token)
        except ValueError:
            return False
        token_lifetime = self.get_token_lifetime(user)
        current_timestamp = int((timezone.now() - datetime.datetime(2001, 1, 1, tzinfo=datetime.UTC)).total_seconds())
        if user.reactivate_until and user.reactivate_until <= timezone.now():
            return False
        if current_timestamp - token_timestamp > token_lifetime:
            return False

        return super().check_token(user, token)


account_activation_token = AccountActivationTokenGenerator()
