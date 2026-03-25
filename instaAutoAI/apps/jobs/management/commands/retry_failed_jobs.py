"""
Management command to retry failed jobs by dispatching Celery tasks.
Uses batched processing to avoid overloading the broker and respects per-job retry limits.
"""

import asyncio
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from celery import current_app
from django.utils import timezone

from instaAutoAI.apps.jobs.models import Job  # adjust import
from core.constants import JOB_STATUS_FAILED


class Command(BaseCommand):
    help = "Retry failed jobs up to a maximum retry count."

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Maximum number of retries per job (default: 3)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of jobs to process per batch (default: 100, max: 1000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show which jobs would be retried without dispatching tasks",
        )
        parser.add_argument(
            "--queue",
            default="celery",
            help="Celery queue to send retry tasks to (default: celery)",
        )
        parser.add_argument(
            "--age-limit",
            type=int,
            default=7,
            help="Only retry jobs failed within the last N days (default: 7)",
        )

    async def handle_async(self, *args, **options):
        max_retries = options["max_retries"]
        batch_size = min(options["batch_size"], 1000)
        dry_run = options["dry_run"]
        queue = options["queue"]
        age_limit_days = options["age_limit"]

        cutoff_date = timezone.now() - timedelta(days=age_limit_days)

        # Query jobs that can be retried
        queryset = Job.objects.filter(
            status=JOB_STATUS_FAILED,
            retry_count__lt=max_retries,
            updated_at__gte=cutoff_date,  # only recent failures
        ).only("id", "retry_count")

        total_count = await sync_to_async(queryset.count)()
        if total_count == 0:
            self.stdout.write(self.style.NOTICE("No eligible jobs found for retry."))
            return

        self.stdout.write(
            f"Found {total_count} jobs eligible for retry (max retries {max_retries}, within {age_limit_days} days)."
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run mode – no tasks will be dispatched."))
            return

        # Process in batches
        success_count = 0
        failed_count = 0

        # Retrieve IDs in batches and dispatch tasks
        offset = 0
        while True:
            batch_ids = await sync_to_async(list)(
                queryset[offset:offset + batch_size].values_list("id", flat=True)
            )
            if not batch_ids:
                break

            for job_id in batch_ids:
                try:
                    # Dispatch Celery task with job ID only (avoid passing model instance)
                    # Assuming a task named 'retry_job' exists in the jobs app
                    current_app.send_task(
                        "instaAutoAI.apps.jobs.tasks.retry_job",
                        args=[job_id],
                        queue=queue,
                        # Use the default retry policy configured on the task itself
                    )
                    success_count += 1
                    self.stdout.write(f"Dispatched retry for job {job_id}")
                except Exception as e:
                    failed_count += 1
                    self.stderr.write(
                        self.style.ERROR(f"Failed to dispatch retry for job {job_id}: {e}")
                    )

            offset += batch_size
            self.stdout.write(f"Processed batch up to {offset} jobs")

        self.stdout.write(
            self.style.SUCCESS(
                f"Retry dispatch completed: {success_count} tasks sent, {failed_count} failed."
            )
        )

        # Optionally, log details for failed dispatches
        if failed_count > 0:
            self.stderr.write(
                self.style.ERROR(
                    "Some tasks could not be dispatched. Check broker availability and task definitions."
                )
            )