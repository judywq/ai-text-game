from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ai_text_game.llm_caller.models import APIRequest
from ai_text_game.llm_caller.models import LLMModel
from ai_text_game.llm_caller.models import QuotaConfig
from ai_text_game.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def active_model():
    model = LLMModel.objects.create(
        name="gpt-4",
        display_name="GPT-4",
        is_active=True,
        is_default=True,
    )
    QuotaConfig.objects.create(
        model=model,
        daily_limit=10,
    )
    return model


class TestActiveModelsView:
    def test_unauthenticated_access(self, api_client):
        url = reverse("active-models")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_active_models(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("active-models")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == active_model.name
        assert data[0]["used_quota"] == 0
        assert data[0]["daily_limit"] == 10  # noqa: PLR2004

    def test_quota_counting(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("active-models")

        # Create some API requests
        APIRequest.objects.create(
            user=user,
            model=active_model,
            essay="Test essay",
            status="COMPLETED",
        )

        # Create an old request that shouldn't count towards today's quota
        yesterday = timezone.now() - timedelta(days=1)
        req = APIRequest.objects.create(
            user=user,
            model=active_model,
            essay="Old essay",
            status="COMPLETED",
        )
        req.created_at = yesterday
        req.save()

        response = client.get(url)
        data = response.json()
        assert data[0]["used_quota"] == 1  # Only today's request counts


class TestAPIRequestViewSet:
    def test_create_request(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("api-request-list")

        data = {
            "essay": "This is a test essay",
            "model_name": active_model.name,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert APIRequest.objects.count() == 1
        request = APIRequest.objects.first()
        assert request.user == user
        assert request.model == active_model
        assert request.essay == data["essay"]
        assert request.status == "PENDING"

    def test_quota_limit(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("api-request-list")

        # Create requests up to the quota limit
        for _ in range(10):
            APIRequest.objects.create(
                user=user,
                model=active_model,
                essay="Test essay",
                status="COMPLETED",
            )

        # Try to create one more request
        data = {
            "essay": "This is a test essay",
            "model_name": active_model.name,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_list_own_requests(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("api-request-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("count") == 0

        # Create some requests for the user
        APIRequest.objects.create(
            user=user,
            model=active_model,
            essay="Test essay 1",
            status="COMPLETED",
        )
        APIRequest.objects.create(
            user=user,
            model=active_model,
            essay="Test essay 2",
            status="PENDING",
        )

        # Create a request for another user
        other_user = UserFactory()
        APIRequest.objects.create(
            user=other_user,
            model=active_model,
            essay="Other user's essay",
            status="COMPLETED",
        )

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("count") == 2  # noqa: PLR2004
