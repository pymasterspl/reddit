import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse_lazy

User = get_user_model()


@pytest.mark.django_db()
def test_swagger_view_user_authenticated(client: Client, user: User) -> None:
    data = {"username": user.email, "password": user.plain_password}
    response = client.post(reverse_lazy("login"), data=data, follow=True)
    assert response.status_code == 200
    response = client.get(reverse_lazy("schema-swagger-ui"))
    assert response.status_code == 200
    response = client.post(reverse_lazy("schema-swagger-ui"))
    assert response.status_code == 405


@pytest.mark.django_db()
def test_swagger_view_user_non_authenticated(client: Client, user: User) -> None:
    response = client.get(reverse_lazy("schema-swagger-ui"))
    assert response.status_code == 403
    response = client.post(reverse_lazy("schema-swagger-ui"))
    assert response.status_code == 405


@pytest.mark.django_db()
def test_redoc_view_user_authenticated(client: Client, user: User) -> None:
    data = {"username": user.email, "password": user.plain_password}
    response = client.post(reverse_lazy("login"), data=data, follow=True)
    assert response.status_code == 200
    response = client.get(reverse_lazy("schema-redoc"))
    assert response.status_code == 200
    response = client.post(reverse_lazy("schema-redoc"))
    assert response.status_code == 405


@pytest.mark.django_db()
def test_redoc_view_user_non_authenticated(client: Client, user: User) -> None:
    response = client.get(reverse_lazy("schema-redoc"))
    assert response.status_code == 403
    response = client.post(reverse_lazy("schema-redoc"))
    assert response.status_code == 405
