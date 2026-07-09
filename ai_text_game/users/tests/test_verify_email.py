import pytest
from allauth.account.internal.flows.email_verification_by_code import (
    EmailVerificationProcess,
)
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_verify_email_with_code(api_client: APIClient):
    register_url = reverse("rest_register")
    verify_url = reverse("rest_verify_email")

    response = api_client.post(
        register_url,
        {
            "email": "verify-test@example.com",
            "username": "verify-test@example.com",
            "password1": "testpass123!",
            "password2": "testpass123!",
            "name": "Verify Test",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    django_request = response.wsgi_request
    process = EmailVerificationProcess.resume(django_request)
    assert process is not None

    response = api_client.post(
        verify_url,
        {"key": process.code},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["detail"] == "ok"


@pytest.mark.django_db
def test_resend_verification_email_refreshes_session(api_client: APIClient):
    register_url = reverse("rest_register")
    resend_url = reverse("rest_resend_email")
    email = "resend-test@example.com"

    response = api_client.post(
        register_url,
        {
            "email": email,
            "username": email,
            "password1": "testpass123!",
            "password2": "testpass123!",
            "name": "Resend Test",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Simulate an expired verification session.
    session = api_client.session
    session.pop("account_email_verification_code", None)
    session.save()

    response = api_client.post(resend_url, {"email": email}, format="json")
    assert response.status_code == status.HTTP_200_OK

    process = EmailVerificationProcess.resume(response.wsgi_request)
    assert process is not None


@pytest.mark.django_db
def test_reregister_unverified_user_resends_code(api_client: APIClient):
    register_url = reverse("rest_register")
    email = "reregister-test@example.com"

    payload = {
        "email": email,
        "username": email,
        "password1": "testpass123!",
        "password2": "testpass123!",
        "name": "Reregister Test",
    }
    response = api_client.post(register_url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    session = api_client.session
    session.pop("account_email_verification_code", None)
    session.save()
    cache.clear()

    payload["password1"] = "newpass123!"
    payload["password2"] = "newpass123!"
    response = api_client.post(register_url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    process = EmailVerificationProcess.resume(response.wsgi_request)
    assert process is not None
