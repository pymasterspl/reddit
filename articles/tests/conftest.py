import pytest
from django.contrib.auth import get_user_model
from faker import Faker


@pytest.fixture()
def user(db: any) -> object:
    user = get_user_model()
    faker = Faker()
    password = faker.password()
    test_user = user.objects.create_user(email="testuser@example.com", nickname="Test Nickname", password=password)
    test_user.plain_password = password
    return test_user
