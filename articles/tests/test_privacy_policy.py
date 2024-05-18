import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db()
def test_privacy_police_view() -> None:
    client = Client()
    url = reverse("privacy-policy")
    http_ok = 200
    response = client.get(url)
    assert response.status_code == http_ok
    assert "privacy-police.html" in [t.name for t in response.templates]
