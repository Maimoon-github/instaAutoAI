import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIClient
from instaAutoAI.apps.jobs.models import GenerationJob

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_jobs(db):
    """Ensure each test starts with an empty jobs table — prevents concurrency
    guard state from leaking between tests."""
    GenerationJob.objects.all().delete()
    yield


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def api_client():
    """DRF API client without authentication."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """DRF API client authenticated with test user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def request_factory():
    """Django request factory for tests."""
    return RequestFactory()


@pytest.fixture
def job(db):
    """Create a queued job."""
    return GenerationJob.objects.create(
        status=GenerationJob.Status.QUEUED,
        request_data={"topic": "test"},
        checkpoint_path="test-thread",
    )


@pytest.fixture
def running_job(db):
    """Create a running job."""
    return GenerationJob.objects.create(
        status=GenerationJob.Status.RUNNING,
        request_data={"topic": "test"},
        checkpoint_path="running-thread",
        celery_task_id="celery-123",
    )


@pytest.fixture
def done_job(db):
    """Create a completed job."""
    return GenerationJob.objects.create(
        status=GenerationJob.Status.DONE,
        request_data={"topic": "test"},
        result_data={"caption": "done"},
        vram_peak_mb=1024.5,
        checkpoint_path="done-thread",
        image_file="jobs/test.png",
    )


@pytest.fixture
def failed_job(db):
    """Create a failed job."""
    return GenerationJob.objects.create(
        status=GenerationJob.Status.FAILED,
        request_data={"topic": "test"},
        error_message="Previous failure",
        checkpoint_path="failed-thread",
    )