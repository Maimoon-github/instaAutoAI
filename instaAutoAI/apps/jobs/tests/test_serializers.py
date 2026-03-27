import pytest
from django.test import RequestFactory
from rest_framework import serializers

from instaAutoAI.apps.jobs.serializers import (
    GenerationRequestSerializer,
    GenerationJobSerializer,
    GenerationJobListSerializer,
    VRAMSnapshotSerializer,
)
from instaAutoAI.apps.jobs.models import GenerationJob
from core.constants import INSTAGRAM_HASHTAG_MIN, INSTAGRAM_HASHTAG_MAX

pytestmark = pytest.mark.django_db


class TestGenerationRequestSerializer:
    valid_data = {
        'topic': 'AI productivity',
        'niche': 'tech',
        'tone': 'professional',
        'output_format': 'image',
        'aspect_ratio': '4:5',
        'caption_length': 'medium',
        'hashtag_count': 20,
        'brand_keywords': ['ai', 'automation']
    }

    def test_valid_data(self):
        serializer = GenerationRequestSerializer(data=self.valid_data)
        assert serializer.is_valid()
        assert serializer.validated_data['topic'] == 'AI productivity'

    def test_missing_required_field(self):
        data = self.valid_data.copy()
        del data['topic']
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'topic' in serializer.errors

    def test_topic_min_length(self):
        data = self.valid_data.copy()
        data['topic'] = 'ab'
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'topic' in serializer.errors

    def test_hashtag_count_out_of_bounds(self):
        data = self.valid_data.copy()
        data['hashtag_count'] = INSTAGRAM_HASHTAG_MIN - 1
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'hashtag_count' in serializer.errors

        data['hashtag_count'] = INSTAGRAM_HASHTAG_MAX + 1
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'hashtag_count' in serializer.errors

    def test_brand_keywords_invalid_characters(self):
        data = self.valid_data.copy()
        data['brand_keywords'] = ['ai#', '@auto']
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'brand_keywords' in serializer.errors

    def test_brand_keywords_empty_list(self):
        data = self.valid_data.copy()
        data['brand_keywords'] = []
        serializer = GenerationRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['brand_keywords'] == []

    def test_output_format_default(self):
        data = self.valid_data.copy()
        del data['output_format']
        serializer = GenerationRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['output_format'] == 'image'

    def test_tone_choices(self):
        data = self.valid_data.copy()
        data['tone'] = 'invalid'
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'tone' in serializer.errors

    def test_validate_topic_strip(self):
        data = self.valid_data.copy()
        data['topic'] = '  trimmed  '
        serializer = GenerationRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['topic'] == 'trimmed'

    def test_validate_topic_blank(self):
        data = self.valid_data.copy()
        data['topic'] = '   '
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'topic' in serializer.errors

    def test_aspect_ratio_choices(self):
        data = self.valid_data.copy()
        data['aspect_ratio'] = 'invalid'
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'aspect_ratio' in serializer.errors

    def test_caption_length_choices(self):
        data = self.valid_data.copy()
        data['caption_length'] = 'invalid'
        serializer = GenerationRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'caption_length' in serializer.errors


class TestGenerationJobSerializer:
    def test_serialization_with_context(self, done_job, request_factory):
        request = request_factory.get('/')
        serializer = GenerationJobSerializer(done_job, context={'request': request})
        data = serializer.data

        assert data['job_id'] == str(done_job.job_id)
        assert data['status'] == GenerationJob.Status.DONE
        assert data['request_data'] == done_job.request_data
        assert data['result_data'] == done_job.result_data
        assert data['image_url'] == request.build_absolute_uri(done_job.image_file.url)
        assert data['video_url'] is None
        assert data['vram_peak_mb'] == 1024.5
        assert data['error_message'] is None

    def test_serialization_without_context(self, done_job):
        serializer = GenerationJobSerializer(done_job)
        data = serializer.data
        assert data['image_url'] is None
        assert data['video_url'] is None

    def test_image_url_missing_file(self, job, request_factory):
        request = request_factory.get('/')
        serializer = GenerationJobSerializer(job, context={'request': request})
        assert serializer.data['image_url'] is None

    def test_video_url(self, done_job, request_factory):
        done_job.video_file = 'jobs/test.mp4'
        done_job.save()
        request = request_factory.get('/')
        serializer = GenerationJobSerializer(done_job, context={'request': request})
        assert 'test.mp4' in serializer.data['video_url']


class TestGenerationJobListSerializer:
    def test_serialization(self, done_job):
        serializer = GenerationJobListSerializer(done_job)
        data = serializer.data
        assert set(data.keys()) == {
            'job_id', 'status', 'vram_peak_mb', 'error_message',
            'created_at', 'completed_at'
        }
        assert 'request_data' not in data
        assert 'result_data' not in data

    def test_error_message_present(self, failed_job):
        serializer = GenerationJobListSerializer(failed_job)
        assert serializer.data['error_message'] == 'Previous failure'


class TestVRAMSnapshotSerializer:
    def test_serialization(self):
        data = {
            'vram_allocated_mb': 512.5,
            'vram_reserved_mb': 1024.0,
            'vram_peak_mb': 768.2,
            'vram_total_mb': 8192.0,
            'timestamp': '2025-03-25T12:00:00Z'
        }
        serializer = VRAMSnapshotSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['vram_allocated_mb'] == 512.5

    def test_missing_required_field(self):
        data = {'vram_allocated_mb': 512.5}
        serializer = VRAMSnapshotSerializer(data=data)
        assert not serializer.is_valid()
        for field in ['vram_reserved_mb', 'vram_peak_mb', 'vram_total_mb', 'timestamp']:
            assert field in serializer.errors

    def test_invalid_timestamp(self):
        data = {
            'vram_allocated_mb': 512.5,
            'vram_reserved_mb': 1024.0,
            'vram_peak_mb': 768.2,
            'vram_total_mb': 8192.0,
            'timestamp': 'not-a-date'
        }
        serializer = VRAMSnapshotSerializer(data=data)
        assert not serializer.is_valid()
        assert 'timestamp' in serializer.errors

    def test_float_validation(self):
        data = {
            'vram_allocated_mb': 'not a float',
            'vram_reserved_mb': 1024.0,
            'vram_peak_mb': 768.2,
            'vram_total_mb': 8192.0,
            'timestamp': '2025-03-25T12:00:00Z'
        }
        serializer = VRAMSnapshotSerializer(data=data)
        assert not serializer.is_valid()
        assert 'vram_allocated_mb' in serializer.errors