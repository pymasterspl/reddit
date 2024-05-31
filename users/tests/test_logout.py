import pytest
from django.urls import reverse


@pytest.fixture
def client_logged_in(client, user):
    client.login(email=user.email, password=user.plain_password)
    return client


@pytest.mark.django_db()
def test_logout_confirmation_view(client_logged_in):
    response = client_logged_in.get(reverse('logout_confirmation'))
    assert response.status_code == 200
    assert "users/logout.html" in [t.name for t in response.templates]


@pytest.mark.django_db()
def test_logout_view(client_logged_in):
    response = client_logged_in.get(reverse('logout'))
    assert response.status_code == 405

    response = client_logged_in.post(reverse('logout'))
    assert response.status_code == 302
    assert response.url == reverse('login')