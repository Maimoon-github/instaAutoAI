import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from instaAutoAI.apps.jobs.models import GenerationJob

pytestmark = pytest.mark.django_db

class TestDashboardView:
    def test_get_dashboard(self, api_client):
        url = reverse('jobs:dashboard')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert b'dashboard.html' in response.content or b'AI Pipeline' in response.content


class TestGenerateView:
    valid_payload = {
        'topic': 'AI productivity',
        'niche': 'tech',
        'tone': 'professional',
        'output_format': 'image',
        'aspect_ratio': '4:5',
        'caption_length': 'medium',
        'hashtag_count': 20,
        'brand_keywords': ['ai', 'automation']
    }

    # def test_requires_authentication(self, api_client):
    #     url = reverse('jobs:job-generate')
    #     response = api_client.post(url, self.valid_payload, format='json')
    #     assert response.status_code == status.HTTP_403_FORBIDDEN



    def test_requires_authentication(self, api_client):
        url = reverse('jobs:job-generate')
        response = api_client.post(
            url,
            self.valid_payload,
            format='json',
            REMOTE_ADDR='8.8.8.8',   # non‑local IP
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 

    def test_authenticated_create_job(self, authenticated_client):
        url = reverse('jobs:job-generate')
        response = authenticated_client.post(url, self.valid_payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'job_id' in data
        assert data['status'] == 'queued'
        job = GenerationJob.objects.get(job_id=data['job_id'])
        assert job.status == GenerationJob.Status.QUEUED
        assert job.request_data == self.valid_payload

    def test_concurrency_limit(self, authenticated_client, user, running_job):
        running_job.user = user
        running_job.save()
        url = reverse('jobs:job-generate')
        response = authenticated_client.post(url, self.valid_payload, format='json')
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.headers.get('Retry-After') == '300'
        assert response.data['error'] == 'pipeline_busy'

    def test_invalid_payload(self, authenticated_client):
        url = reverse('jobs:job-generate')
        response = authenticated_client.post(url, {'topic': ''}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestJobDetailView:
    def test_get_job_detail(self, authenticated_client, job):
        url = reverse('jobs:job-detail', args=[job.job_id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['job_id'] == str(job.job_id)
        assert response.data['status'] == job.status

    def test_job_not_found(self, authenticated_client):
        url = reverse('jobs:job-detail', args=['00000000-0000-0000-0000-000000000000'])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_uuid_format(self, authenticated_client):
        # Django's <uuid:job_id> converter rejects non-UUID strings at routing
        # time and returns 404 — it never reaches the view.
        response = authenticated_client.get('/api/v1/jobs/not-a-uuid/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobListView:
    def test_list_jobs(self, authenticated_client, job, done_job, failed_job):
        url = reverse('jobs:job-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['count'] >= 3
        assert 'results' in data
        assert 'next' in data
        assert 'previous' in data
        for item in data['results']:
            assert 'request_data' not in item
            assert 'result_data' not in item

    def test_filter_by_status(self, authenticated_client, job, running_job, done_job):
        url = reverse('jobs:job-list') + '?status=running'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['status'] == 'running'

    def test_filter_by_date_range(self, authenticated_client, job):
        GenerationJob.objects.create(
            status=GenerationJob.Status.QUEUED,
            request_data={},
            created_at=timezone.now() - timedelta(days=10)
        )
        url = reverse('jobs:job-list') + f'?created_after={timezone.now() - timedelta(days=5):%Y-%m-%d}'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        job_ids = [item['job_id'] for item in response.data['results']]
        assert str(job.job_id) in job_ids

    def test_pagination(self, authenticated_client):
        for _ in range(25):
            GenerationJob.objects.create(status=GenerationJob.Status.QUEUED, request_data={})
        url = reverse('jobs:job-list')
        response = authenticated_client.get(url)
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None

    def test_max_page_size(self, authenticated_client):
        url = reverse('jobs:job-list') + '?page_size=200'
        response = authenticated_client.get(url)
        assert len(response.data['results']) <= 100


class TestJobVRAMView:
    def test_get_vram_snapshot(self, authenticated_client, job):
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.memory_allocated', return_value=512 * 1024**2), \
             patch('torch.cuda.memory_reserved', return_value=1024 * 1024**2), \
             patch('torch.cuda.max_memory_allocated', return_value=768 * 1024**2), \
             patch('torch.cuda.get_device_properties') as mock_props:
            mock_props.return_value.total_memory = 8 * 1024**3
            url = reverse('jobs:job-vram', args=[job.job_id])
            response = authenticated_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            data = response.data
            assert data['vram_allocated_mb'] == 512.0
            assert data['vram_reserved_mb'] == 1024.0
            assert data['vram_peak_mb'] == 768.0
            assert data['vram_total_mb'] == 8192.0
            assert 'timestamp' in data

    def test_vram_snapshot_without_gpu(self, authenticated_client, job):
        with patch('torch.cuda.is_available', return_value=False):
            url = reverse('jobs:job-vram', args=[job.job_id])
            response = authenticated_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            data = response.data
            assert data['vram_allocated_mb'] == 0.0
            assert data['vram_total_mb'] == 0.0

    def test_vram_snapshot_exception(self, authenticated_client, job):
        with patch('torch.cuda.is_available', side_effect=ImportError):
            url = reverse('jobs:job-vram', args=[job.job_id])
            response = authenticated_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            data = response.data
            assert data['vram_allocated_mb'] == 0.0