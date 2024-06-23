import pytest
from django.contrib.auth import get_user_model
from faker import Faker

@pytest.fixture
def user(db):
    User = get_user_model()
    faker = Faker()
    password = faker.password()
    user = User.objects.create_user(
        email="testuser@example.com", nickname="Test Nickname", password=password
    )
    user.plain_password = password
    return user
