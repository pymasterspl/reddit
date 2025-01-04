from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User


class Command(BaseCommand):
    help = "Anonymize inactive users"

    def handle(self: "Command", *_args: str, **__options: str) -> None:
        users_to_anonymize = User.objects.filter(
            is_active=False,
            deactivated_at__isnull=False,
            reactivate_until__isnull=False,
            reactivate_until__lte=timezone.now() - timezone.timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT),
            anonymized_at__isnull=True,
        )
        for user in users_to_anonymize:
            user.anonymize_account()
            self.stdout.write(f"Anonymized user: {user.nickname}")
        self.stdout.write("Anonymization complete.")
