"""
Management command to delete old completed jobs in batches.
Uses batched ID slicing to avoid memory exhaustion and OFFSET/LIMIT pagination issues.
"""

import asyncio
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async

from instaAutoAI.apps.jobs.models import Job  # adjust import to actual model
from core.constants import JOB_STATUS_DONE, JOB_STATUS_FAILED  # from earlier constants


class Command(BaseCommand):
    help = "Purge jobs older than a specified number of days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete jobs older than this many days (default: 30)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of jobs to delete per batch (default: 1000, max: 10000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--status",
            default=f"{JOB_STATUS_DONE},{JOB_STATUS_FAILED}",
            help="Comma-separated list of statuses to purge (default: done,failed)",
        )

    async def handle_async(self, *args, **options):
        days = options["days"]
        batch_size = min(options["batch_size"], 10000)  # safety cap
        dry_run = options["dry_run"]
        status_list = [s.strip() for s in options["status"].split(",")]

        cutoff_date = timezone.now() - timedelta(days=days)

        # Query the IDs of jobs to purge
        queryset = Job.objects.filter(
            status__in=status_list,
            updated_at__lt=cutoff_date,
        ).only("id")

        # Count total
        total_count = await sync_to_async(queryset.count)()
        if total_count == 0:
            self.stdout.write(self.style.NOTICE("No jobs eligible for purging."))
            return

        self.stdout.write(
            f"Found {total_count} jobs older than {days} days with status {status_list}."
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run mode – no deletions performed."))
            return

        # Fetch IDs in batches and delete
        deleted_total = 0
        while True:
            # Get next batch of IDs
            ids = await sync_to_async(list)(
                queryset[:batch_size].values_list("id", flat=True)
            )
            if not ids:
                break

            # Wrap deletion in a transaction for atomicity of the batch
            async def delete_batch():
                with transaction.atomic():
                    # Use a synchronous ORM call inside transaction.atomic()
                    # (transaction.atomic doesn't work with async ORM)
                    return await sync_to_async(Job.objects.filter(id__in=ids).delete)()

            deleted_batch = await delete_batch()
            deleted_count = deleted_batch[0] if isinstance(deleted_batch, tuple) else deleted_batch
            deleted_total += deleted_count

            self.stdout.write(f"Deleted batch of {deleted_count} jobs (total {deleted_total})")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully purged {deleted_total} jobs.")
        )