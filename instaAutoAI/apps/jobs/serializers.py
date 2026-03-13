from rest_framework import serializers

from core.constants import (
    ASPECT_RATIO_DIMENSIONS,
    INSTAGRAM_HASHTAG_MAX,
    INSTAGRAM_HASHTAG_MIN,
)

from .models import GenerationJob


# ── Input serializer ──────────────────────────────────────────────────────────

class GenerationRequestSerializer(serializers.Serializer):
    """
    Validates POST /api/v1/generate/ request bodies.

    All fields map directly to GenerationRequest TypedDict consumed by
    the LangGraph pipeline.  Validated data is stored verbatim in
    GenerationJob.request_data.
    """

    ASPECT_RATIO_CHOICES = list(ASPECT_RATIO_DIMENSIONS.keys())
    OUTPUT_FORMAT_CHOICES = ["image", "reel", "both"]
    CAPTION_LENGTH_CHOICES = ["short", "medium", "long"]
    TONE_CHOICES = [
        "professional",
        "casual",
        "humorous",
        "inspirational",
        "informative",
        "gen-z",
        "luxury",
    ]

    topic = serializers.CharField(
        min_length=3,
        max_length=200,
        help_text="Content topic, e.g. 'AI productivity hacks'.",
    )
    niche = serializers.CharField(
        min_length=2,
        max_length=100,
        help_text="Target niche, e.g. 'tech lifestyle'.",
    )
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES,
        help_text="Caption and strategy tone.",
    )
    output_format = serializers.ChoiceField(
        choices=OUTPUT_FORMAT_CHOICES,
        default="image",
        help_text="'image', 'reel', or 'both'.",
    )
    aspect_ratio = serializers.ChoiceField(
        choices=ASPECT_RATIO_CHOICES,
        default="4:5",
        help_text="Instagram aspect ratio.",
    )
    caption_length = serializers.ChoiceField(
        choices=CAPTION_LENGTH_CHOICES,
        default="medium",
    )
    hashtag_count = serializers.IntegerField(
        min_value=INSTAGRAM_HASHTAG_MIN,
        max_value=INSTAGRAM_HASHTAG_MAX,
        default=20,
        help_text=f"Number of hashtags ({INSTAGRAM_HASHTAG_MIN}–{INSTAGRAM_HASHTAG_MAX}).",
    )
    brand_keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        max_length=10,
        help_text="Optional brand voice anchor keywords (no # or @ symbols).",
    )

    def validate_brand_keywords(self, value: list[str]) -> list[str]:
        for kw in value:
            if "#" in kw or "@" in kw:
                raise serializers.ValidationError(
                    "Brand keywords must not contain # or @ characters."
                )
        return value

    def validate_topic(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Topic must not be blank.")
        return value.strip()


# ── Output serializers ────────────────────────────────────────────────────────

class GenerationJobSerializer(serializers.ModelSerializer):
    """
    Full serializer for GenerationJob — used by GET /api/v1/jobs/{id}/.

    image_url and video_url return absolute URLs so the frontend can
    render assets without constructing paths.  Requires
    context={"request": request} when instantiated.
    """

    image_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = GenerationJob
        fields = [
            "job_id",
            "status",
            "request_data",
            "result_data",
            "image_url",
            "video_url",
            "vram_peak_mb",
            "error_message",
            "celery_task_id",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields  # all fields read-only on output serializer

    def get_image_url(self, obj: GenerationJob) -> str | None:
        request = self.context.get("request")
        if obj.image_file and request:
            return request.build_absolute_uri(obj.image_file.url)
        return None

    def get_video_url(self, obj: GenerationJob) -> str | None:
        request = self.context.get("request")
        if obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None


class GenerationJobListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for GET /api/v1/jobs/ list view.
    Omits large JSON blobs (request_data, result_data) for fast pagination.
    """

    class Meta:
        model = GenerationJob
        fields = [
            "job_id",
            "status",
            "vram_peak_mb",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class VRAMSnapshotSerializer(serializers.Serializer):
    """Payload for GET /api/v1/jobs/{id}/vram/ live snapshot endpoint."""

    vram_allocated_mb = serializers.FloatField()
    vram_reserved_mb  = serializers.FloatField()
    vram_peak_mb      = serializers.FloatField()
    vram_total_mb     = serializers.FloatField()
    timestamp         = serializers.DateTimeField()