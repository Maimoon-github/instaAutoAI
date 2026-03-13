import django_filters

from .models import GenerationJob


class GenerationJobFilter(django_filters.FilterSet):
    """
    Filter backend for GET /api/v1/jobs/.

    Supports filtering by status, output_format extracted from
    request_data JSON, and date range on created_at.

    Apply in views:
        filterset_class = GenerationJobFilter
        filter_backends = [DjangoFilterBackend, OrderingFilter]
    """

    # Status exact match
    status = django_filters.ChoiceFilter(
        choices=GenerationJob.Status.choices,
    )

    # Date range on created_at
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Created after (ISO-8601)",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Created before (ISO-8601)",
    )

    class Meta:
        model = GenerationJob
        fields = ["status", "created_after", "created_before"]