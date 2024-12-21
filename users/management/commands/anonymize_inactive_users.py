from django.core.management.base import BaseCommand
from django.utils.timezone import now

from users.models import User


class Command(BaseCommand):
    help = "Anonymize inactive users"

    def handle(self, *args, **kwargs):
        users = User.objects.filter(
            is_active=False,
            deactivated_at__isnull=False,
            reactivate_until__lte=now()
        )
        for user in users:
            user.anonymize_account()
            self.stdout.write(f"Anonymized user: {user.id}")
        self.stdout.write("Anonymization complete.")
