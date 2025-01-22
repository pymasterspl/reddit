from typing import Any

from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta

from users.models import User


class Command(BaseCommand):
    help = "Clear expired pending email requests"

    def handle(self: "Command", *_args: tuple, **__kwargs: dict[str, Any]) -> None:
        expiration_time = now() - timedelta(hours=72)
        expired_users = User.objects.filter(pending_email_created__lt=expiration_time)

        count = expired_users.count()
        expired_users.update(pending_email=None, pending_email_created=None)
        self.stdout.write(f"Cleared {count} expired pending email requests.")
