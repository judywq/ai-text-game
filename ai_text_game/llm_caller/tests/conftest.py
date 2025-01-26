import pytest
from rest_framework.test import APIClient

from ai_text_game.users.tests.factories import UserFactory


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(user, api_client):
    api_client.force_authenticate(user=user)
    return api_client
