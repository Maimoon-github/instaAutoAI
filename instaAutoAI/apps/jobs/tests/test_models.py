import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

from instaAutoAI.apps.jobs.models import GenerationJob
from core.constants import JOB_STATUS_QUEUED, JOB_STATUS_RUNNING, JOB_STATUS_DONE, JOB_STATUS_FAILED


pytestmark = pytest.mark.django_db


class TestGenerationJob:
    def test_create_job(self, job):
        assert job.job_id is not None
        assert job.status == GenerationJob.Status.QUEUED
        assert job.created_at is not None
        assert job.completed_at is None

    def test_status_choices(self):
        for status in [JOB_STATUS_QUEUED, JOB_STATUS_RUNNING, JOB_STATUS_DONE, JOB_STATUS_FAILED]:
            assert status in dict(GenerationJob.Status.choices)

    def test_mark_running(self, job):
        celery_id = "abc123"
        job.mark_running(celery_task_id=celery_id)
        assert job.status == GenerationJob.Status.RUNNING
        assert job.celery_task_id == celery_id
        assert job.completed_at is None

    def test_mark_done(self, job):
        result = {'caption': 'Great post!'}
        job.mark_done(result_data=result, image_path='jobs/test.png', vram_peak_mb=2048.5)
        assert job.status == GenerationJob.Status.DONE
        assert job.result_data == result
        assert job.image_file.name == 'jobs/test.png'
        assert job.vram_peak_mb == 2048.5
        assert job.completed_at is not None

    def test_mark_failed(self, job):
        error = "GPU out of memory"
        job.mark_failed(error)
        assert job.status == GenerationJob.Status.FAILED
        assert job.error_message == error
        assert job.completed_at is not None

    def test_reset_for_retry(self, failed_job):
        failed_job.reset_for_retry()
        assert failed_job.status == GenerationJob.Status.QUEUED
        assert failed_job.error_message is None
        assert failed_job.completed_at is None

    def test_str_representation(self, job):
        assert str(job) == f"{job.job_id} ({job.status})"

    @pytest.mark.asyncio
    async def test_async_create(self):
        # Test async ORM compatibility (requires sync_to_async for writes)
        job = await sync_to_async(GenerationJob.objects.create)(
            request_data={'topic': 'async test'}
        )
        assert job.job_id is not None

    def test_default_ordering(self):
        from datetime import timedelta
        job1 = JobFactory(created_at=timezone.now())
        job2 = JobFactory(created_at=timezone.now() + timedelta(hours=1))
        jobs = list(GenerationJob.objects.all())
        # Should be ordered by -created_at (most recent first)
        assert jobs[0].created_at > jobs[1].created_at

    def test_indexes(self):
        # Quick sanity check: the meta indexes are defined
        indexes = [idx.name for idx in GenerationJob._meta.indexes]
        assert "jobs_generationjob_status_created_at" in indexes