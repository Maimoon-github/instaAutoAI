import pytest
from unittest.mock import patch, Mock
from celery.exceptions import Retry
from asgiref.sync import sync_to_async

from instaAutoAI.apps.jobs.tasks import execute_pipeline
from instaAutoAI.apps.jobs.models import GenerationJob
from instaAutoAI.apps.pipeline.runner import run_pipeline


pytestmark = pytest.mark.django_db


class TestExecutePipeline:
    @patch('instaAutoAI.apps.jobs.tasks._run_pipeline_async')
    def test_task_success(self, mock_run_async, job):
        # Setup mock to do nothing
        mock_run_async.return_value = None
        job_id = str(job.job_id)
        request_data = {'topic': 'test'}

        execute_pipeline(job_id, request_data)

        # Verify job marked running, then run_pipeline called, and job not marked failed
        job.refresh_from_db()
        assert job.status == GenerationJob.Status.RUNNING  # because the task marks running before async call
        # In real code, mark_done would be called inside run_pipeline. Here we mock, so status remains running.
        # But we can check that run_pipeline was called
        mock_run_async.assert_called_once_with(job_id, request_data)

    @patch('instaAutoAI.apps.jobs.tasks._run_pipeline_async')
    def test_task_exception_handling(self, mock_run_async, job):
        # Simulate exception in pipeline
        mock_run_async.side_effect = Exception("GPU error")
        job_id = str(job.job_id)
        request_data = {'topic': 'test'}

        execute_pipeline(job_id, request_data)

        # Job should be marked failed
        job.refresh_from_db()
        assert job.status == GenerationJob.Status.FAILED
        assert "GPU error" in job.error_message

    @patch('instaAutoAI.apps.jobs.tasks._run_pipeline_async')
    def test_task_handles_missing_job(self, mock_run_async):
        # Non-existent job ID
        job_id = "00000000-0000-0000-0000-000000000000"
        request_data = {}
        execute_pipeline(job_id, request_data)
        # No exception, just log; mock_run_async should not be called
        mock_run_async.assert_not_called()

    def test_task_idempotency(self, job):
        # If a task is retried after job already done, it should not reprocess
        job.mark_done(result_data={})
        job_id = str(job.job_id)
        with patch('instaAutoAI.apps.jobs.tasks._run_pipeline_async') as mock_run:
            execute_pipeline(job_id, {})
            # Since job is done, we should not call run_pipeline again
            mock_run.assert_not_called()
        # Status should remain done
        job.refresh_from_db()
        assert job.status == GenerationJob.Status.DONE

    @patch('instaAutoAI.apps.jobs.tasks._run_pipeline_async')
    def test_task_marks_running_before_async(self, mock_run_async, job):
        job_id = str(job.job_id)
        execute_pipeline(job_id, {})
        # Ensure job is marked running even if async part fails later
        job.refresh_from_db()
        assert job.status == GenerationJob.Status.RUNNING