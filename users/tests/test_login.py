
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db()
def test_login_page_loads_correctly(client: Client):
    login_url = reverse("login")
    response = client.get(login_url)
    assert "users/login.html" in [t.name for t in response.templates]

    
@pytest.mark.django_db()
def test_login_view(client: Client, user: User):
    login_url = reverse('login')
    data = {
        "username": user.username,
        "password": user.plain_password
    }
    response = client.post(login_url, data)
    assert response.status_code == 302  # Redirect after successful login
    assert response.url == reverse("home-page")
    user = response.wsgi_request.user
    assert user.is_authenticated
    