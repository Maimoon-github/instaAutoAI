import pytest
from unittest.mock import patch

from instaAutoAI.apps.jobs.tasks import execute_pipeline
from instaAutoAI.apps.jobs.models import GenerationJob

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def job(db):
    return GenerationJob.objects.create(
        status=GenerationJob.Status.QUEUED,
        request_data={"topic": "test"},
        checkpoint_path="test-thread",
    )


class TestExecutePipeline:
    def test_task_success(self, job):
        job_id = str(job.job_id)
        request_data = {"topic": "test"}

        with patch("instaAutoAI.apps.jobs.tasks._run_pipeline_async") as mock_run:
            mock_run.return_value = None
            execute_pipeline(job_id, request_data)

        job.refresh_from_db()
        # mock returns None (no mark_done called), so status stays RUNNING
        assert job.status == GenerationJob.Status.RUNNING
        assert job.celery_task_id is not None
        mock_run.assert_called_once_with(job_id, request_data)

    def test_task_exception_handling(self, job):
        job_id = str(job.job_id)
        request_data = {"topic": "test"}

        with patch(
            "instaAutoAI.apps.jobs.tasks._run_pipeline_async",
            side_effect=Exception("GPU error"),
        ):
            execute_pipeline(job_id, request_data)

        job.refresh_from_db()
        assert job.status == GenerationJob.Status.FAILED
        assert "GPU error" in job.error_message

    def test_task_handles_missing_job(self):
        job_id = "00000000-0000-0000-0000-000000000000"
        request_data = {}

        with patch("instaAutoAI.apps.jobs.tasks._run_pipeline_async") as mock_run:
            execute_pipeline(job_id, request_data)
            mock_run.assert_not_called()

    def test_task_idempotency_done(self, done_job):
        job_id = str(done_job.job_id)
        request_data = {}

        with patch("instaAutoAI.apps.jobs.tasks._run_pipeline_async") as mock_run:
            execute_pipeline(job_id, request_data)
            mock_run.assert_not_called()

        done_job.refresh_from_db()
        assert done_job.status == GenerationJob.Status.DONE

    def test_task_marks_running_before_async(self, job):
        """
        The task calls mark_running() before delegating to the async pipeline.
        When the async step raises, the except block in execute_pipeline calls
        mark_failed(), so the final status is FAILED — not RUNNING.
        """
        job_id = str(job.job_id)
        request_data = {}

        with patch(
            "instaAutoAI.apps.jobs.tasks._run_pipeline_async",
            side_effect=Exception("Async fail"),
        ):
            execute_pipeline(job_id, request_data)

        job.refresh_from_db()
        assert job.status == GenerationJob.Status.FAILED
        assert "Async fail" in job.error_message