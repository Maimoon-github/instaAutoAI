import pytest
import factory
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIClient
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async

from instaAutoAI.apps.jobs.models import GenerationJob
from instaAutoAI.config.asgi import application

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for Django User model."""
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

    class Meta:
        model = User
        django_get_or_create = ('username',)


class JobFactory(factory.django.DjangoModelFactory):
    """Factory for GenerationJob model."""
    job_id = factory.Faker('uuid4')
    status = GenerationJob.Status.QUEUED
    request_data = factory.Dict({
        'topic': 'AI productivity',
        'niche': 'tech',
        'tone': 'professional',
        'output_format': 'image',
        'aspect_ratio': '4:5',
        'caption_length': 'medium',
        'hashtag_count': 20,
        'brand_keywords': ['ai', 'automation']
    })
    result_data = None
    image_file = None
    video_file = None
    vram_peak_mb = None
    error_message = None
    celery_task_id = None
    checkpoint_path = None

    class Meta:
        model = GenerationJob
        skip_postgeneration_save = True  # avoid saving in post-generation hooks


@pytest.fixture
def user(db):
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def job(db):
    """Create a test job."""
    return JobFactory()


@pytest.fixture
def running_job(db):
    """Create a job that is running."""
    job = JobFactory(status=GenerationJob.Status.RUNNING)
    return job


@pytest.fixture
def done_job(db):
    """Create a completed job."""
    job = JobFactory(
        status=GenerationJob.Status.DONE,
        result_data={'caption': 'Test caption'},
        image_file='jobs/2025/01/test.png',
        video_file=None,
        vram_peak_mb=1024.5,
        completed_at=timezone.now()
    )
    return job


@pytest.fixture
def failed_job(db):
    """Create a failed job."""
    job = JobFactory(
        status=GenerationJob.Status.FAILED,
        error_message='Model loading failed'
    )
    return job


@pytest.fixture
def api_client():
    """DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def request_factory():
    """Django RequestFactory for view unit tests."""
    return RequestFactory()


@pytest.fixture
def websocket_communicator():
    """Return a configured WebsocketCommunicator for job progress."""
    async def _communicator(job_id):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/jobs/{job_id}/"
        )
        return communicator
    return _communicator


@pytest.fixture
def mock_torch(monkeypatch):
    """Mock torch.cuda for VRAM snapshot tests."""
    import torch
    class MockCuda:
        def is_available(self):
            return True
        def memory_allocated(self):
            return 512 * 1024 * 1024  # 512 MB
        def memory_reserved(self):
            return 1024 * 1024 * 1024  # 1 GB
        def max_memory_allocated(self):
            return 768 * 1024 * 1024  # 768 MB
        def get_device_properties(self, device):
            class Props:
                total_memory = 8 * 1024 * 1024 * 1024  # 8 GB
            return Props()
    monkeypatch.setattr(torch, 'cuda', MockCuda())