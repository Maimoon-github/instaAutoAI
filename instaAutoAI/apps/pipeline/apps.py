"""
Django AppConfig for the pipeline app.

This module is synchronous – all async initialisation is deferred
to the runner (first call). We only import nodes to register them
with LangGraph (side effects) and set up signals if needed.
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

# Guard to prevent double execution in dev server autoreload
_ready_executed = False


class PipelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pipeline"
    verbose_name = "Content Pipeline"

    def ready(self) -> None:
        global _ready_executed
        if _ready_executed:
            return

        # Import nodes to ensure they are registered with LangGraph.
        # This also triggers any side effects (like decorators) in the nodes.
        from . import nodes  # noqa: F401

        # Register signals if needed
        # from .signals import ...  # not yet created

        logger.info("Pipeline app ready (node modules loaded)")

        _ready_executed = True