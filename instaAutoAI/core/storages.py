"""
Custom storage backends for job assets.
"""

import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class JobAssetsStorage(FileSystemStorage):
    """
    Storage for job-generated media files.
    Files are stored under MEDIA_ROOT/jobs/<job_id>/.
    """
    def __init__(self, **kwargs):
        location = kwargs.pop("location", None) or os.path.join(settings.MEDIA_ROOT, "jobs")
        base_url = kwargs.pop("base_url", None) or os.path.join(settings.MEDIA_URL, "jobs")
        super().__init__(location=location, base_url=base_url, **kwargs)

    def get_available_name(self, name, max_length=None):
        """
        If a file with the same name already exists, append a UUID instead of overwriting.
        """
        if self.exists(name):
            dir_name, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            unique_id = uuid.uuid4().hex[:8]
            name = os.path.join(dir_name, f"{file_root}_{unique_id}{file_ext}")
        return super().get_available_name(name, max_length)


@deconstructible
class OverwriteStorage(FileSystemStorage):
    """
    Storage that allows overwriting existing files.
    Use with caution: set allow_overwrite=True.
    """
    allow_overwrite = False

    def __init__(self, allow_overwrite=False, **kwargs):
        self.allow_overwrite = allow_overwrite
        super().__init__(**kwargs)

    def get_available_name(self, name, max_length=None):
        if self.allow_overwrite and self.exists(name):
            # Return the same name to overwrite
            return name
        return super().get_available_name(name, max_length)


class SecureStorageMixin:
    """
    Mixin to add encryption before saving files (placeholder for future cloud integration).
    """
    def _save(self, name, content):
        # TODO: implement encryption before saving
        return super()._save(name, content)

    def _open(self, name, mode="rb"):
        # TODO: implement decryption when reading
        return super()._open(name, mode)