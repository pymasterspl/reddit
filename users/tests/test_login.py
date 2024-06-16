import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.test import Client
from django.urls import reverse_lazy

from users.tests.test_user_model import HTTP_SUCCESS

User = get_user_model()


@pytest.mark.django_db()
def test_login_user_view_post_success_authenticated(client: Client, user: User) -> None:
    data = {"username": user.email, "password": user.plain_password}
    response = client.post(reverse_lazy("login"), data=data, follow=True)
    assert response.status_code == HTTP_SUCCESS
    user = response.context["user"]
    assert user.is_authenticated
    assert response.wsgi_request.user.is_authenticated


def test_login_user_view_post_missing_credentials(client: Client) -> None:
    data = {}
    response = client.post(reverse_lazy("login"), data=data)
    assert response.status_code == HTTP_SUCCESS
    form = AuthenticationForm(data=data)
    form.is_valid()
    assert form.errors.get("username") == ["This field is required."]
    assert form.errors.get("password") == ["This field is required."]
