from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.timezone import now, timedelta
from six import text_type

from users.models import User


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self: "AccountActivationTokenGenerator", user: User, timestamp: int) -> str:
        return text_type(user.pk) + text_type(timestamp)


account_activation_token = AccountActivationTokenGenerator()


class EmailChangeTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self: "EmailChangeTokenGenerator", user: User, timestamp: int) -> str:
        return (
            text_type(user.pk)
            + text_type(timestamp)
            + text_type(user.pending_email)
            + text_type(user.pending_email_created)
        )

    def is_token_expired(self: "EmailChangeTokenGenerator", user: User, expiration_hours: int = 72) -> bool:
        if not user.pending_email_created:
            return True
        expiration_time = user.pending_email_created + timedelta(hours=expiration_hours)
        return now() > expiration_time


email_change_token = EmailChangeTokenGenerator()
