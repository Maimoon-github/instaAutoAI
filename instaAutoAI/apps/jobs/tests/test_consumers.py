import pytest
import json
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from django.utils import timezone
from instaAutoAI.config.asgi import application
from instaAutoAI.apps.jobs.consumers import emit_progress
from instaAutoAI.apps.jobs.models import GenerationJob

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.asyncio,
]


@pytest.fixture
async def job():
    job = await sync_to_async(GenerationJob.objects.create)(
        status=GenerationJob.Status.QUEUED,
        request_data={"topic": "test"},
        checkpoint_path="test-thread",
    )
    return job


class TestJobProgressConsumer:
    async def test_consumer_connect(self, job):
        communicator = WebsocketCommunicator(application, f"/ws/jobs/{job.job_id}/")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_consumer_connect_invalid_job_id(self):
        # The Channels router uses a <uuid:job_id> path converter. A non-UUID
        # path segment does not match any route, so the router raises ValueError.
        with pytest.raises(ValueError, match="No route found for path"):
            communicator = WebsocketCommunicator(application, "/ws/jobs/invalid/")
            await communicator.connect()

    async def test_consumer_receives_progress(self, job):
        communicator = WebsocketCommunicator(application, f"/ws/jobs/{job.job_id}/")
        await communicator.connect()

        await emit_progress(str(job.job_id), node="strategy", progress=50, status="running")

        response = await communicator.receive_json_from()
        assert response["node"] == "strategy"
        assert response["progress"] == 50
        assert response["status"] == "running"
        assert "timestamp" in response

        await communicator.disconnect()

    async def test_consumer_ignores_client_messages(self, job):
        communicator = WebsocketCommunicator(application, f"/ws/jobs/{job.job_id}/")
        await communicator.connect()

        await communicator.send_to(text_data=json.dumps({"type": "ping"}))
        # No response expected; just ensure no exception.
        await communicator.disconnect()

    async def test_emit_progress_no_channel_layer(self, monkeypatch, job):
        from instaAutoAI.apps.jobs import consumers

        monkeypatch.setattr(consumers, "get_channel_layer", lambda: None)

        # Should not raise
        await emit_progress(str(job.job_id), node="test", progress=10)

    async def test_emit_progress_with_extra(self, job):
        communicator = WebsocketCommunicator(application, f"/ws/jobs/{job.job_id}/")
        await communicator.connect()

        await emit_progress(
            str(job.job_id),
            node="image_gen",
            progress=75,
            extra={"vram": 2048},
        )

        response = await communicator.receive_json_from()
        assert response["extra"]["vram"] == 2048
        await communicator.disconnect()