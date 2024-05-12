import pytest
from django.urls import reverse
from django.test import Client


@pytest.mark.django_db
def test_privacy_police_view():
    client = Client()
    url = reverse('privacy-policy')
    response = client.get(url)
    assert response.status_code == 200
    assert "privacy-police.html" in [t.name for t in response.templates]