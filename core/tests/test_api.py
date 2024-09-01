import pytest
from django.test.client import Client
from django.urls import reverse

from conftest import CommunityWithMembersFixture, CreateCommunitiesFixture, create_posts
from core.models import Community, Post

pytestmark = pytest.mark.django_db


PAGE_SIZE = 10
PREFIX = "http://testserver"


def get_abs_url(url: str, page: int) -> str:
    return f"{PREFIX}{url}?page={page}"


visible_privacies = [Community.PUBLIC, Community.RESTRICTED]


def validate_three_pages_pagination(url: str, client: Client) -> None:
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
    assert page_1_response.data["next"] == page_2_abs_url
    assert page_2_response.data["previous"] in (endpoint_abs_url, page_1_abs_url)
    assert page_2_response.data["next"] == page_3_abs_url
    assert page_3_response.data["previous"] == page_2_abs_url
    assert page_3_response.data["next"] is None
    assert page_1_response.data["count"] == 2 * PAGE_SIZE + 1
    assert page_2_response.data["count"] == 2 * PAGE_SIZE + 1
    assert page_3_response.data["count"] == 2 * PAGE_SIZE + 1


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_communities_list_three_pages(
    client: Client, create_communities: CreateCommunitiesFixture, privacy: str
) -> None:
    create_communities(count=PAGE_SIZE * 2 + 1, posts_per_community=0, privacy=privacy)
    url = reverse("api-communities-list")
    validate_three_pages_pagination(url, client)


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_posts_three_pages(client: Client, create_communities: CreateCommunitiesFixture, privacy: str) -> None:
    create_communities(count=1, posts_per_community=2 * PAGE_SIZE + 1, privacy=privacy)
    url = reverse("api-posts-list-view")
    validate_three_pages_pagination(url, client)


def test_api_communities_list_private(client: Client, create_communities: CreateCommunitiesFixture) -> None:
    create_communities(count=10, posts_per_community=2, privacy=Community.PRIVATE)
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_community_posts_three_pages(
    client: Client, create_communities: CreateCommunitiesFixture, privacy: str
) -> None:
    tested_community = create_communities(count=1, posts_per_community=2 * PAGE_SIZE + 1, privacy=privacy)[0]
    url = reverse("api-communities-posts-list", kwargs={"slug": tested_community.slug})
    validate_three_pages_pagination(url, client)


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_communities_list_ten(client: Client, create_communities: CreateCommunitiesFixture, privacy: str) -> None:
    create_communities(count=10, posts_per_community=0, privacy=privacy)
    response = client.get(reverse("api-communities-list"))
    assert Community.objects.count() == 10
    assert Post.objects.count() == 0
    assert response.status_code == 200
    results = response.data["results"]
    assert isinstance(results, list)
    assert len(results) == 10
    for community_data in results:
        assert set(community_data.keys()) == {"id", "name", "slug"}


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_communities_list_mixed(client: Client, create_communities: CreateCommunitiesFixture, privacy: str) -> None:
    create_communities(count=5, posts_per_community=2, privacy=Community.PRIVATE)  # These should be ignored
    public_communities = create_communities(count=5, posts_per_community=2, privacy=privacy)
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert len(response.data["results"]) == 5
    assert all(comm["id"] in [c.id for c in public_communities] for comm in response.data["results"])


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_posts_list_ten(client: Client, create_communities: CreateCommunitiesFixture, privacy: str) -> None:
    create_communities(count=2, posts_per_community=5, privacy=privacy)
    response = client.get(reverse("api-posts-list-view"))
    assert response.status_code == 200
    results = response.data["results"]
    assert isinstance(results, list)
    assert len(results) == 10
    assert set(response.data["results"][0].keys()) == {
        # no Post.version field
        "id",
        "score",
        "is_active",
        "is_locked",
        "created_at",
        "updated_at",
        "title",
        "content",
        "up_votes",
        "down_votes",
        "display_counter",
        "author",
        "community",
        "parent",
    }


def test_api_posts_list_private_community(client: Client, create_communities: CreateCommunitiesFixture) -> None:
    create_communities(count=5, posts_per_community=2, privacy=Community.PRIVATE)
    response = client.get(reverse("api-posts-list-view"))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_posts_list_empty(client: Client) -> None:
    response = client.get(reverse("api-posts-list-view"))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_community_list_one_restricted(client: Client, restricted_community: Community) -> None:
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert restricted_community.id == response.data["results"][0]["id"]
    assert set(response.data["results"][0].keys()) == {"id", "name", "slug"}


def test_api_community_list_one_public(client: Client, public_community: Community) -> None:
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert public_community.id == response.data["results"][0]["id"]
    assert set(response.data["results"][0].keys()) == {"id", "name", "slug"}


def test_api_community_list_empty(client: Client) -> None:
    response = client.get(reverse("api-communities-list"))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_community_get_one_public(
    client: Client, public_community_with_members: CommunityWithMembersFixture
) -> None:
    community = public_community_with_members(5)
    response = client.get(reverse("api-community-detail", kwargs={"slug": community.slug}))
    assert response.status_code == 200
    assert response.data["id"] == community.id
    assert len(response.data["members"]) == 5
    assert set(response.data.keys()) == {
        "id",
        "name",
        "slug",
        "members",
        "count_online_users",
        "author",
        "is_active",
        "is_locked",
        "privacy",
        "created_at",
        "updated_at",
        "is_18_plus",
    }


def test_api_community_get_one_restricted(
    client: Client, restricted_community_with_members: CommunityWithMembersFixture
) -> None:
    community = restricted_community_with_members(5)
    response = client.get(reverse("api-community-detail", kwargs={"slug": community.slug}))
    assert response.status_code == 200
    assert response.data["id"] == community.id
    assert len(response.data["members"]) == 5
    assert set(response.data.keys()) == {
        "id",
        "name",
        "slug",
        "members",
        "count_online_users",
        "author",
        "is_active",
        "is_locked",
        "privacy",
        "created_at",
        "updated_at",
        "is_18_plus",
    }


def test_api_community_get_one_private(client: Client, private_community: Community) -> None:
    response = client.get(reverse("api-community-detail", kwargs={"slug": private_community.slug}))
    assert response.status_code == 200
    assert response.data["id"] == private_community.id
    assert set(response.data.keys()) == {"id", "name", "slug"}


@pytest.mark.parametrize("privacy", visible_privacies)
def test_api_community_posts_get_list(client: Client, community: Community, privacy: str) -> None:
    create_posts(community, count=3)
    other_community = Community.objects.create(name="Ruby Community")
    create_posts(other_community, count=4, start_idx=4)
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": community.slug}))
    result = response.data["results"]
    assert len(result) == 3
    assert response.status_code == 200


def test_api_community_posts_get_empty(client: Client, community: Community) -> None:
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": community.slug}))
    assert response.status_code == 200
    assert response.data["results"] == []


def test_api_community_posts_non_existing_community(client: Client) -> None:
    non_existing_slug = "a-b-c-d-e-f-slug"
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": non_existing_slug}))
    assert response.status_code == 404


def test_api_community_posts_private(client: Client, private_community: Community) -> None:
    create_posts(private_community, 10)
    response = client.get(reverse("api-communities-posts-list", kwargs={"slug": private_community.slug}))
    assert response.status_code == 403
