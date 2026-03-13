from rest_framework.pagination import CursorPagination, PageNumberPagination


class JobPagination(PageNumberPagination):
    """
    Standard page-number pagination for the job history list.

    Default page size is 20 — enough for the dashboard sidebar without
    over-fetching.  Clients may request up to 100 per page.
    """

    page_size              = 20
    page_size_query_param  = "page_size"
    max_page_size          = 100


class JobCursorPagination(CursorPagination):
    """
    Cursor-based pagination for real-time job status polling.

    Cursor pagination is stable under high-frequency inserts — a
    page-number cursor never skips or duplicates rows when new jobs
    arrive between requests, making it safe for the live dashboard
    job stream.

    Ordered by descending creation time so newest jobs surface first.
    """

    page_size             = 20
    ordering              = "-created_at"
    cursor_query_param    = "cursor"