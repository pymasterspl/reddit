import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from faker import Faker

from users.tokens import account_activation_token

User = get_user_model()
fake = Faker()

@pytest.mark.django_db()
def test_registration_view(client: Client) -> None:
    url = reverse("register")
    data = {
        "nickname": "testnickname",
        "email": "testuser@gmail.com",
        "password1": "strong_password",
        "password2": "strong_password",
    }
    response = client.post(url, data)

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert User.objects.filter(email="testuser@gmail.com").exists()
    user = User.objects.get(email="testuser@gmail.com")
    assert not user.is_active


@pytest.mark.django_db()
def test_activate_user_view(client: Client) -> None:
    password = fake.password()
    user = User.objects.create_user(nickname="testnickname",
                                    email="testuser@example.com",
                                    password=password)
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    activation_url = reverse("activate-account",
                             kwargs={"uidb64": uid, "token": token})
    response = client.get(activation_url)

    assert response.status_code == 302
    assert response.url == reverse("login")
    user.refresh_from_db()
    assert user.is_active

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    message = messages[0]
    assert message.message == "Your account has been activated, you can now login!"
