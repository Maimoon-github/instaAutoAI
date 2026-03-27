import pytest
from django.urls import reverse
from rest_framework.test import APIClient


# Apply django_db marker to every test in this module.
pytestmark = pytest.mark.django_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def active_user(django_user_model):
    """
    Create and return a standard active user.

    Uses pytest-django's built-in django_user_model fixture which resolves
    AUTH_USER_MODEL automatically — never imports User directly.
    """
    return django_user_model.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="StrongPass123!",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

ME_URL = "/api/v1/me/"


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_me_returns_200_for_authenticated_user(api_client, active_user):
    """
    Authenticated users receive 200 OK with their profile data.
    """
    api_client.force_authenticate(user=active_user)
    response = api_client.get(ME_URL)

    assert response.status_code == 200


def test_me_returns_403_for_unauthenticated_request(api_client):
    """
    Unauthenticated requests must receive 403 Forbidden.

    DRF returns 403 (not 401) when no authentication credentials are
    provided and the default authentication scheme is SessionAuthentication
    or BasicAuthentication.
    """
    response = api_client.get(ME_URL)

    assert response.status_code == 403


def test_me_response_excludes_password(api_client, active_user):
    """
    The response payload must never contain the 'password' key.

    Leaking even a hashed password via the API is a security violation.
    """
    api_client.force_authenticate(user=active_user)
    response = api_client.get(ME_URL)

    assert "password" not in response.data


def test_me_response_contains_expected_fields(api_client, active_user):
    """
    Response JSON contains exactly the four expected fields and no others.
    """
    api_client.force_authenticate(user=active_user)
    response = api_client.get(ME_URL)

    expected_keys = {"id", "username", "email", "date_joined"}

    assert set(response.data.keys()) == expected_keys


def test_me_response_values_match_user(api_client, active_user):
    """
    Serialized field values match the actual user record.
    """
    api_client.force_authenticate(user=active_user)
    response = api_client.get(ME_URL)

    assert response.data["id"] == active_user.pk
    assert response.data["username"] == active_user.username
    assert response.data["email"] == active_user.email


def test_me_endpoint_is_read_only(api_client, active_user):
    """
    POST, PUT, PATCH, DELETE must return 405 Method Not Allowed —
    the /me/ endpoint is intentionally read-only.
    """
    api_client.force_authenticate(user=active_user)

    assert api_client.post(ME_URL, {}).status_code == 405
    assert api_client.put(ME_URL, {}).status_code == 405
    assert api_client.patch(ME_URL, {}).status_code == 405
    assert api_client.delete(ME_URL).status_code == 405