import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from faker import Faker

from users.tokens import account_activation_token

User = get_user_model()
fake = Faker()


@pytest.mark.django_db()
def test_api_activate_user_view_response_success(client: Client) -> None:
    password = fake.password()
    user = User.objects.create_user(nickname="testnickname", email="testuser@example.com", password=password)
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    activation_url = reverse("api-activate-account", kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 202
    assert response.data == {"message": "Your account has been activated, you can now login!"}
    user.refresh_from_db()
    assert user.is_active


@pytest.mark.django_db()
def test_api_double_activate_user_view_response_failed(client: Client) -> None:
    password = fake.password()
    user = User.objects.create_user(nickname="testnickname", email="testuser@example.com", password=password)
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    activation_url = reverse("api-activate-account", kwargs={"uidb64": uid, "token": token})
    client.get(activation_url)
    response = client.get(activation_url)

    assert response.status_code == 400
    assert response.data == {"message": "Invalid activation link or account already activated!"}
    user.refresh_from_db()
    assert user.is_active


@pytest.mark.django_db()
def test_api_invalid_user_view_response_failed(client: Client) -> None:
    password = fake.password()
    fake_user = User.objects.create_user(nickname="testnickname123", email="testuser123@example.com", password=password)
    user = User.objects.create_user(nickname="testnickname", email="testuser@example.com", password=password)
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(fake_user.pk))
    token = account_activation_token.make_token(fake_user)

    activation_url = reverse("api-activate-account", kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 400
    assert response.data == {"message": "Invalid activation link or account already activated!"}
    user.refresh_from_db()
    assert not user.is_active


@pytest.mark.django_db()
def test_api_invalid_token_view_response_failed(client: Client) -> None:
    password = fake.password()
    user = User.objects.create_user(nickname="testnickname", email="testuser@example.com", password=password)
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user) + "123"

    activation_url = reverse("api-activate-account", kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 400
    assert response.data == {"message": "Invalid activation link or account already activated!"}
    user.refresh_from_db()
    assert not user.is_active
