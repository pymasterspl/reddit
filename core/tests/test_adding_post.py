import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from ..models import Post, Community

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture()
def user(client: Client) -> User:
    user = User.objects.create_user(username='test_user', password='test_password')
    client.login(email=user.email, password=user.password)
    return user


@pytest.fixture()
def community() -> Community:
    return Community.objects.create(name='Test Community', is_active=True)


def test_add_post_valid(client: Client, user: User, community: Community) -> None:
    data = {
        'community': community.pk,
        'title': 'Test Post Title',
        'content': 'This is a test post content.',
    }
    response = client.post(reverse('add_post'), data=data, follow=True)
    assert response.status_code == 200
    assert response.context['post'].author == user
    assert response.context['post'].title == data['title']
    assert response.context['post'].content == data['content']


def test_add_post_invalid(client: Client, user: User, community: Community) -> None:
    data = {'title': ''}  # Missing content
    response = client.post(reverse('add_post'), data=data)
    assert response.status_code == 200
    assert b'This field is required.' in response.content.encode()


def test_add_post_unauthorized(client: Client, community: Community) -> None:
    data = {
        'community': community.pk,
        'title': 'Test Post Title',
        'content': 'This is a test post content.',
    }
    response = client.post(reverse('add_post'), data=data)
    # Assert redirection to login page (replace 302 with actual redirect code if different)
    assert response.status_code == 302
    assert reverse('login') in response.url
