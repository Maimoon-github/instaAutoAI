import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from instaAutoAI.apps.jobs.models import GenerationJob
from instaAutoAI.apps.jobs.views import _get_vram_snapshot

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestDashboardView:
    def test_get_dashboard(self, api_client):
        url = reverse('dashboard')  # adjust URL name
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert b'dashboard.html' in response.content or 'dashboard' in response.template_name


class TestGenerateView:
    @pytest.fixture
    def valid_payload(self):
        return {
            'topic': 'AI productivity',
            'niche': 'tech',
            'tone': 'professional',
            'output_format': 'image',
            'aspect_ratio': '4:5',
            'caption_length': 'medium',
            'hashtag_count': 20,
            'brand_keywords': ['ai', 'automation']
        }

    def test_requires_authentication(self, api_client, valid_payload):
        url = reverse('generate')
        response = api_client.post(url, valid_payload, format='json')
        # Permission class IsLocalOrAuthenticated allows local requests, but we are using client with no auth
        # Actually, IsLocalOrAuthenticated checks if request is from localhost; for test, client is not local.
        # It should return 403.
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_create_job(self, authenticated_client, valid_payload):
        url = reverse('generate')
        response = authenticated_client.post(url, valid_payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'job_id' in data
        assert data['status'] == 'queued'
        # Verify job exists in DB
        job = GenerationJob.objects.get(job_id=data['job_id'])
        assert job.status == GenerationJob.Status.QUEUED
        assert job.request_data == valid_payload

    def test_concurrency_limit(self, authenticated_client, valid_payload, running_job):
        # Create a running job for the same user (the permission is user-based)
        # We need to ensure the user is the same. Our authenticated_client uses the user from fixture.
        # We'll attach the job to that user. The job factory creates jobs without user, but we can add user.
        user = authenticated_client.handler._force_user
        running_job.user = user
        running_job.save()
        url = reverse('generate')
        response = authenticated_client.post(url, valid_payload, format='json')
        # Should return 503 with Retry-After
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.headers.get('Retry-After') == '300'
        assert response.data['error'] == 'pipeline_busy'

    def test_invalid_payload(self, authenticated_client):
        url = reverse('generate')
        response = authenticated_client.post(url, {'topic': ''}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestJobDetailView:
    def test_get_job_detail(self, authenticated_client, job):
        url = reverse('job-detail', args=[job.job_id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['job_id'] == str(job.job_id)
        assert response.data['status'] == job.status

    def test_job_not_found(self, authenticated_client):
        url = reverse('job-detail', args=['00000000-0000-0000-0000-000000000000'])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data


class TestJobListView:
    def test_list_jobs(self, authenticated_client, job, done_job, failed_job):
        url = reverse('job-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 3
        # Check pagination keys
        assert 'results' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data

    def test_filter_by_status(self, authenticated_client, job, running_job, done_job):
        url = reverse('job-list') + '?status=running'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['status'] == 'running'

    def test_filter_by_date_range(self, authenticated_client, job):
        from django.utils import timezone
        from datetime import timedelta
        # Create a job older than a week
        old_job = JobFactory(created_at=timezone.now() - timedelta(days=10))
        url = reverse('job-list') + f'?created_after={timezone.now() - timedelta(days=5):%Y-%m-%d}'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        job_ids = [item['job_id'] for item in response.data['results']]
        assert str(job.job_id) in job_ids
        assert str(old_job.job_id) not in job_ids

    def test_pagination(self, authenticated_client, job):
        # Create 25 jobs (default page_size=20)
        for _ in range(25):
            JobFactory()
        url = reverse('job-list')
        response = authenticated_client.get(url)
        assert len(response.data['results']) == 20
        # Check next page exists
        assert response.data['next'] is not None

    def test_max_page_size(self, authenticated_client):
        url = reverse('job-list') + '?page_size=200'
        response = authenticated_client.get(url)
        # Should limit to max 100
        assert response.data['page_size'] == 100


class TestJobVRAMView:
    def test_get_vram_snapshot(self, authenticated_client, job, mock_torch):
        url = reverse('job-vram', args=[job.job_id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'vram_allocated_mb' in data
        assert 'vram_reserved_mb' in data
        assert 'vram_peak_mb' in data
        assert 'vram_total_mb' in data
        assert 'timestamp' in data

    def test_vram_snapshot_without_gpu(self, authenticated_client, job, monkeypatch):
        # Mock torch to report no GPU
        import torch
        monkeypatch.setattr(torch, 'cuda', None)  # Simulate no cuda
        url = reverse('job-vram', args=[job.job_id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['vram_allocated_mb'] == 0.0
        assert data['vram_total_mb'] == 0.0