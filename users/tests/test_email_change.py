from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.timezone import now
from faker import Faker
from freezegun import freeze_time

from users.tokens import account_activation_token, email_change_token

User = get_user_model()
fake = Faker()


@pytest.mark.django_db()
def test_change_email_view(client: Client, user: User) -> None:
    url = reverse("email_change")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert "users/email_change.html" in [t.name for t in response.templates]


@pytest.mark.django_db()
def test_email_change_success(client: Client, user: User) -> None:
    new_email = "new_email@example.com"
    url = reverse("email_change")
    client.force_login(user)
    response = client.post(url, {"old_email": user.email, "new_email": new_email, "new_email_confirmation": new_email})
    user.refresh_from_db()
    assert user.pending_email == new_email
    assert user.pending_email_created
    assert response.status_code == 302
    assert len(mail.outbox) == 1


@pytest.mark.django_db()
def test_email_change_same_email_failed(client: Client, user: User) -> None:
    url = reverse("email_change")
    client.force_login(user)
    response = client.post(
        url, {"old_email": user.email, "new_email": user.email, "new_email_confirmation": user.email}
    )
    user.refresh_from_db()
    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db()
def test_confirm_change_email_request_response_success(client: Client, user: User) -> None:
    user.pending_email = "changedemail@example.com"
    assert user.email != user.pending_email
    user.pending_email_created = now()
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_change_token.make_token(user)

    activation_url = reverse("confirm-email-change", kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 302
    user.refresh_from_db()
    assert not user.pending_email
    assert not user.pending_email_created
    assert user.email == "changedemail@example.com"


@pytest.mark.django_db()
def test_double_confirm_change_email_request_view_response_failed(client: Client, user: User) -> None:
    user.pending_email = "changedemail@example.com"
    assert user.email != user.pending_email
    user.pending_email_created = now()
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_change_token.make_token(user)
    activation_url = reverse("confirm-email-change", kwargs={"uidb64": uid, "token": token})
    client.get(activation_url)
    response = client.get(activation_url)

    assert response.status_code == 200
    user.refresh_from_db()
    assert not user.pending_email
    assert not user.pending_email_created
    assert user.email == "changedemail@example.com"


@pytest.mark.django_db()
def test_invalid_user_change_email_request_response_failed(client: Client, user: User) -> None:
    user.pending_email = "changedemail@example.com"
    assert user.email != user.pending_email
    user.pending_email_created = now()
    fake_user = User.objects.create_user(
        nickname="testnickname123", email="testuser123@example.com", password=fake.password()
    )
    user.save()

    uid = urlsafe_base64_encode(force_bytes(fake_user.pk))
    token = account_activation_token.make_token(fake_user)

    activation_url = reverse("confirm-email-change", kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.pending_email == "changedemail@example.com"
    assert user.pending_email_created
    assert user.email != "changedemail@example.com"


@pytest.mark.django_db()
def test_invalid_token_view_response_failed(client: Client, user: User) -> None:
    user.pending_email = "changedemail@example.com"
    assert user.email != user.pending_email
    user.pending_email_created = now()
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = f"{account_activation_token.make_token(user)}123"

    activation_url = reverse("confirm-email-change", kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.pending_email == "changedemail@example.com"
    assert user.pending_email_created
    assert user.email != "changedemail@example.com"


@pytest.mark.django_db()
def test_email_change_token_expiration(user: User) -> None:
    new_email = fake.email()

    token = email_change_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    with freeze_time(now() + timedelta(hours=73)):
        client = Client()
        response = client.get(reverse("confirm-email-change", kwargs={"uidb64": uid, "token": token}))
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email != new_email
