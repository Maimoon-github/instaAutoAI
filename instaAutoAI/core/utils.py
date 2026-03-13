"""
Helper functions used across the project.
"""

import hashlib
import uuid
import re
from django.conf import settings
from django.utils.crypto import get_random_string


def get_job_media_path(instance, filename):
    """
    Callable for FileField.upload_to to organize files by job ID.
    Example: jobs/<job_id>/filename.ext
    """
    return f"jobs/{instance.job_id}/{filename}"


def truncate_caption(text, max_length=2200):
    """
    Truncate caption to max_length, ideally at a sentence boundary.
    """
    if len(text) <= max_length:
        return text
    # Try to cut at last period, question mark, or exclamation within limit
    candidates = [".", "!", "?"]
    cut_pos = -1
    for punct in candidates:
        pos = text.rfind(punct, 0, max_length)
        if pos > cut_pos:
            cut_pos = pos
    if cut_pos > 0:
        return text[: cut_pos + 1]
    # Fallback to simple truncation
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def generate_unique_id(prefix="job"):
    """
    Generate a unique ID with optional prefix.
    Uses timestamp + random string.
    """
    timestamp = uuid.uuid1().hex[:10]  # time-based
    rand = get_random_string(6)
    return f"{prefix}_{timestamp}_{rand}"


def format_hashtags(hashtag_list):
    """
    Ensure each hashtag starts with '#' and remove duplicates.
    """
    formatted = []
    seen = set()
    for tag in hashtag_list:
        tag = tag.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        if tag.lower() not in seen:
            seen.add(tag.lower())
            formatted.append(tag)
    return formatted


def get_client_ip(request):
    """
    Extract real client IP address from request headers,
    accounting for proxies.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def vram_to_human_readable(bytes_value):
    """
    Convert bytes to a human-readable string (MB/GB).
    """
    if bytes_value >= 1024**3:
        return f"{bytes_value / 1024**3:.2f} GB"
    elif bytes_value >= 1024**2:
        return f"{bytes_value / 1024**2:.2f} MB"
    else:
        return f"{bytes_value} B"


def generate_hash(data):
    """
    Generate a SHA‑256 hash of the input data (string or bytes).
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()