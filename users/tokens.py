import six
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from users.models import User
from django.conf import settings


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self: "AccountActivationTokenGenerator", user: User, timestamp: int) -> str:
        return six.text_type(user.pk) + six.text_type(timestamp)

    def get_token_lifetime(self: "AccountActivationTokenGenerator", user: User) -> int:
        if user.reactivate_until and user.reactivate_until > timezone.now():
            delta = user.reactivate_until - timezone.now()
            return int(delta.total_seconds())
        return settings.RESET_PASSWORD_TIMEOUT

    def check_token(self: "AccountActivationTokenGenerator", user: User, token) -> bool:
        token_lifetime = self.get_token_lifetime(user)
        timestamp = self._num_seconds(self._now()) - self._num_seconds(self._make_timestamp(user))
        if timestamp > token_lifetime:
            return False
        return super().check_token(user, token)


account_activation_token = AccountActivationTokenGenerator()
