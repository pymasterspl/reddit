import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db()
def test_password_reset_view(
        client: Client,
) -> None:
    url = reverse("reset_password")
    response = client.get(url)
    assert response.status_code == 200
    assert "users/reset_password.html" in [t.name for t in response.templates]


@pytest.mark.django_db()
def test_password_reset_not_send_email(
        client: Client,
        generated_password: str,
) -> None:
    test_email = "test@example.com"
    User.objects.create_user(email="testuser@example.com",
                             password=generated_password)
    url = reverse("reset_password")
    response = client.post(url, {"email": test_email})
    assert response.status_code == 302
    assert len(mail.outbox) == 0


@pytest.mark.django_db()
def test_password_reset_send_email(
        client: Client,
        generated_password: str,
) -> None:
    test_email = "test@example.com"
    user = User.objects.create_user(email=test_email, password=generated_password)
    url = reverse("reset_password")
    response = client.post(url, {"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 1


@pytest.mark.django_db()
def test_password_reset_twice_send_email(
        client: Client,
        generated_password: str,
) -> None:
    test_email = "test@example.com"
    user = User.objects.create_user(email=test_email, password=generated_password)
    url = reverse("reset_password")
    response = client.post(url, {"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    url = reverse("reset_password")
    response = client.post(url, {"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 2


@pytest.mark.django_db()
def test_password_first_wrong_mail_and_second_correct(
        client: Client,
        generated_password: str,
) -> None:
    test_email = "test1@example.com"
    user = User.objects.create_user(email="test@example.com", password=generated_password)
    url = reverse("reset_password")
    response = client.post(url, {"email": test_email})
    assert response.status_code == 302
    assert len(mail.outbox) == 0
    url = reverse("reset_password")
    response = client.post(url, {"email": user.email})
    assert response.status_code == 302
    assert len(mail.outbox) == 1
