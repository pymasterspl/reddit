import pytest
import reddit.settings as settings
from django.urls import reverse
from conftest import create_posts, create_communities
from core.models import Community, Post
from urllib.parse import urlparse



pytestmark = pytest.mark.django_db


PAGE_SIZE = 10
PREFIX = "http://testserver"


def get_abs_url(url, page):
    return f"{PREFIX}{url}?page={page}"


def test_pagination_size():
    assert settings.REST_FRAMEWORK["PAGE_SIZE"] == PAGE_SIZE
    assert settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'] == "rest_framework.pagination.PageNumberPagination"


def three_pages_pagination(url, client):
    page_1_response = client.get(url)
    page_2_response = client.get(page_1_response.data["next"])
    page_3_response = client.get(page_2_response.data["next"])
    
    endpoint_abs_url = f"{PREFIX}{url}"
    page_1_abs_url = get_abs_url(url, page=1)
    page_2_abs_url = get_abs_url(url, page=2)
    page_3_abs_url = get_abs_url(url, page=3)
    
    assert page_1_response.status_code == 200
    assert page_2_response.status_code == 200
    assert page_3_response.status_code == 200
    assert len(page_1_response.data["results"]) == PAGE_SIZE
    assert len(page_2_response.data["results"]) == PAGE_SIZE
    assert len(page_3_response.data["results"]) == 1
    assert page_1_response.data["previous"] is None
    assert page_1_response.data['next'] == page_2_abs_url
    assert page_2_response.data["previous"] in (endpoint_abs_url, page_1_abs_url)
    assert page_2_response.data["next"] == page_3_abs_url
    assert page_3_response.data["previous"] == page_2_abs_url
    assert page_3_response.data["next"] is None
    assert page_1_response.data["count"] == 2 * PAGE_SIZE + 1
    assert page_2_response.data["count"] == 2 * PAGE_SIZE + 1
    assert page_3_response.data["count"] == 2 * PAGE_SIZE + 1

def test_api_communities_list_three_pages(client, create_communities):
    create_communities(count=PAGE_SIZE*2+1, posts_per_community=0)
    url = reverse("api-communities-list")
    three_pages_pagination(url, client)

def test_api_posts_three_pages(client, create_communities):
    create_communities(count=1, posts_per_community=2*PAGE_SIZE+1)
    url = reverse("api-posts-list-view")
    three_pages_pagination(url, client)

def test_api_communities_list_private(client, create_communities):
    create_communities(count=10, posts_per_community=2, privacy=Community.PRIVATE)
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert response.data["results"] == []

def test_api_community_posts_three_pages(client, create_communities):
    tested_community = create_communities(count=1, posts_per_community=2*PAGE_SIZE+1)[0]
    url = reverse("api-communities-posts-list", kwargs={"slug": tested_community.slug})
    three_pages_pagination(url, client)

def test_api_communities_list_ten(client, create_communities):
    create_communities(count=10, posts_per_community=0)
    response = client.get(reverse("api-communities-list"))
    assert Community.objects.count() == 10
    assert Post.objects.count() == 0
    assert response.status_code == 200
    results = response.data["results"]
    assert isinstance(results, list)
    assert len(results) == 10

def test_api_posts_list_ten(client, create_communities):
    create_communities(count=2, posts_per_community=5)
    response = client.get(reverse("api-posts-list-view"))
    assert response.status_code == 200
    results = response.data["results"]
    assert isinstance(results, list)
    assert len(results) == 10

def test_api_posts_list_private_community(client, create_communities):
    create_communities(count=5, posts_per_community=2, privacy=Community.PRIVATE)
    response = client.get(reverse("api-posts-list-view"))
    assert response.status_code == 200
    assert response.data["results"] == []

def test_api_posts_list_empty(client):
    response = client.get(reverse("api-posts-list-view"))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_community_list_one(client, community):
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert community.id == response.data["results"][0]["id"]


def test_api_community_list_empty(client):
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_community_get_one(client, public_community_with_members):
    community = public_community_with_members(5)
    response = client.get(reverse("api-community-detail", kwargs={"slug": community.slug}))
    assert response.status_code == 200
    assert response.data["id"] == community.id
    assert len(response.data["members"]) == 5
    assert "author" in response.data

def test_api_community_get_one_private(client, private_community):
    response = client.get(reverse("api-community-detail", kwargs={"slug": private_community.slug}))
    assert response.status_code == 200
    assert response.data["id"] == private_community.id
    assert not "members" in response.data
    assert not "author" in response.data


def test_api_community_posts_get_list(client, community):
    create_posts(community, count=3)   
    other_community = Community.objects.create(name="Ruby Community")
    create_posts(other_community, count=4, start_idx=4)
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": community.slug}))
    result = response.data["results"]
    assert len(result) == 3
    assert response.status_code == 200


def test_api_community_posts_get_empty(client, community):
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": community.slug}))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_community_posts_non_existing_community(client):
    NON_EXISTING_SLUG = "a-b-c-d-e-f-slug"
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": NON_EXISTING_SLUG}))
    assert response.status_code == 404


def test_api_community_posts_private(client, private_community):
    create_posts(private_community, 10)
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": private_community.slug}))
    assert response.status_code == 403
