#!/usr/bin/env python
"""
Database seeder for initial admin user and test data.

Usage:
    python scripts/seed_db.py               # seed data
    python scripts/seed_db.py --flush       # flush and seed fresh data
"""

import os
import sys
import argparse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django
django.setup()

User = get_user_model()
from instaAutoAI.apps.jobs.models import GenerationJob


def seed_admin():
    """Create admin user if not exists."""
    admin_exists = User.objects.filter(username="admin").exists()
    if not admin_exists:
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123"
        )
        print("✓ Admin user created (username: admin, password: admin123)")
    else:
        print("✓ Admin user already exists")


def seed_sample_jobs():
    """Create a few sample jobs for development."""
    # Skip if already have jobs
    if GenerationJob.objects.count() > 0:
        print("✓ Sample jobs already exist, skipping")
        return

    sample_data = [
        {
            "request_data": {
                "topic": "AI in healthcare",
                "niche": "medical technology",
                "tone": "professional",
                "output_format": "image",
                "aspect_ratio": "4:5",
                "caption_length": "medium",
                "hashtag_count": 15,
                "brand_keywords": ["AI", "healthcare"]
            },
            "status": GenerationJob.Status.DONE,
            "result_data": {"caption": "Sample result"},
            "vram_peak_mb": 1024.5,
            "completed_at": timezone.now()
        },
        {
            "request_data": {
                "topic": "Eco-friendly products",
                "niche": "sustainability",
                "tone": "inspirational",
                "output_format": "video",
                "aspect_ratio": "9:16",
                "caption_length": "short",
                "hashtag_count": 20,
                "brand_keywords": ["green", "eco"]
            },
            "status": GenerationJob.Status.FAILED,
            "error_message": "VRAM OOM",
            "completed_at": timezone.now()
        },
    ]
    for data in sample_data:
        job = GenerationJob.objects.create(**data)
        print(f"✓ Created job {job.job_id} ({job.status})")


def flush_data():
    """Flush all data from the database."""
    print("Flushing database...")
    call_command("flush", "--noinput")
    print("✓ Database flushed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--flush", action="store_true", help="Flush database before seeding")
    args = parser.parse_args()

    if args.flush:
        flush_data()

    seed_admin()
    seed_sample_jobs()
    print("\n✅ Seeding complete.")