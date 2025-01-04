import six
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from users.models import User


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self: "AccountActivationTokenGenerator", user: User, timestamp: int) -> str:
        return six.text_type(user.pk) + six.text_type(timestamp)


account_activation_token = AccountActivationTokenGenerator()
