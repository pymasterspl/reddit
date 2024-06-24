from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from users.models import User


@pytest.mark.django_db()
def test_is_online(user: User, settings: list, client: Client) -> None:
    settings.LAST_ACTIVITY_ONLINE_LIMIT_MINUTES = 15
    # Initially, the user's last_activity should be datetime.now
    assert user.is_online

    user.last_activity = timezone.now() - timedelta(minutes=5)
    user.save()
    assert user.is_online

    user.last_activity = timezone.now() - timedelta(minutes=16)
    user.save()
    assert not user.is_online

    client.force_login(user)
    client.get(reverse("home"))
    user.refresh_from_db()

    assert user.is_online


@pytest.mark.django_db()
def test_last_activity_ago(user: User) -> None:
    # Initially, the user's last_activity should be datetime.now
    assert user.last_activity_ago == "just now"

    # Update last_activity to a recent time
    user.last_activity = timezone.now() - timedelta(seconds=30)
    user.save()
    assert user.last_activity_ago == "just now"

    user.last_activity = timezone.now() - timedelta(minutes=5)
    user.save()
    assert user.last_activity_ago == "5 minutes ago"

    user.last_activity = timezone.now() - timedelta(hours=2)
    user.save()
    assert user.last_activity_ago == "2 hours ago"

    user.last_activity = timezone.now() - timedelta(days=1)
    user.save()
    assert user.last_activity_ago == "1 day ago"

    user.last_activity = timezone.now() - timedelta(days=3)
    user.save()
    assert user.last_activity_ago == "3 days ago"
