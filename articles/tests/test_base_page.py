import pytest
from django.urls import reverse
from django.test import Client


@pytest.mark.django_db
def test_privacy_police_view():
    client = Client()
    url = reverse('home-page')
    response = client.get(url)
    assert response.status_code == 200
    assert "base.html" in [t.name for t in response.templates]