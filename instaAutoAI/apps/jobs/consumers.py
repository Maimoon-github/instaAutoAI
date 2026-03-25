"""
WebSocket consumer for real-time pipeline progress streaming.

Architecture
------------
One `JobProgressConsumer` instance is created per WebSocket connection.
Each consumer joins the channel group ``job_{job_id}`` on connect and
leaves on disconnect.  Pipeline nodes (running inside a Celery worker)
call the module-level helper ``emit_progress()`` which uses
``get_channel_layer().group_send()`` to broadcast across process
boundaries through Redis.

Channels type-to-handler routing
---------------------------------
The ``type`` field in a ``group_send`` payload uses DOTS  (``job.progress``).
The corresponding handler method uses UNDERSCORES (``job_progress``).
Mismatching these two causes *silent* event drops — the most common
Channels bug.  Both names are kept in sync by the constant
``EVENT_TYPE`` defined at the bottom of this file.
"""
import json
import logging
from datetime import datetime, timezone

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Channel layer event type — dots in group_send, underscores as method name.
_EVENT_TYPE_DOT  = "job.progress"    # used in group_send payload
_EVENT_TYPE_METH = "job_progress"    # must match the handler method name below


def _group_name(job_id: str) -> str:
    """Return the channel group name for a given job UUID string."""
    return f"job_{job_id}"


# ── Consumer ──────────────────────────────────────────────────────────────────

class JobProgressConsumer(AsyncWebsocketConsumer):
    """
    One instance per WebSocket client.  Streams ``job.progress`` events
    to the connected browser while the pipeline runs.

    The consumer is read-only from the client's perspective — inbound
    messages (``receive``) are silently ignored.  All data flows from
    the Celery pipeline → Redis channel layer → this consumer → browser.
    """

    async def connect(self) -> None:
        self.job_id    = self.scope["url_route"]["kwargs"]["job_id"]
        self.group_key = _group_name(self.job_id)

        # Guard: channel_layer is None when CHANNEL_LAYERS is misconfigured.
        if self.channel_layer is None:
            logger.error(
                "channel_layer is None — check CHANNEL_LAYERS setting. "
                "Closing WebSocket for job %s.",
                self.job_id,
            )
            await self.close(code=1011)
            return

        await self.channel_layer.group_add(self.group_key, self.channel_name)
        await self.accept()
        logger.debug("WS connected: job=%s channel=%s", self.job_id, self.channel_name)

    async def disconnect(self, close_code: int) -> None:
        # Always discard even if connect() closed early — group_discard is
        # idempotent and will not raise if the channel was never added.
        if self.channel_layer is not None:
            await self.channel_layer.group_discard(self.group_key, self.channel_name)
        logger.debug(
            "WS disconnected: job=%s code=%s", self.job_id, close_code
        )

    async def receive(self, text_data: str = "", bytes_data: bytes = b"") -> None:
        # This is a server-push–only stream.  Client messages are ignored.
        pass

    # ── Channel layer event handler ───────────────────────────────────────────
    # Method name MUST match _EVENT_TYPE_DOT with dots replaced by underscores.

    async def job_progress(self, event: dict) -> None:
        """
        Receive a ``job.progress`` event from the channel layer and
        forward it as a JSON text frame to the connected WebSocket client.
        """
        payload = {
            "node":      event.get("node"),
            "progress":  event.get("progress"),
            "status":    event.get("status", "running"),
            "timestamp": event.get("timestamp"),
            "extra":     event.get("extra", {}),
        }
        await self.send(text_data=json.dumps(payload))


# ── Module-level broadcast helper ─────────────────────────────────────────────

async def emit_progress(
    job_id: str,
    node: str,
    progress: int,
    status: str = "running",
    extra: dict | None = None,
) -> None:
    """
    Broadcast a progress event to all WebSocket clients subscribed to
    the job's channel group.

    Called by pipeline nodes inside the Celery worker process.  Uses
    ``get_channel_layer()`` (not ``self.channel_layer``) because there
    is no consumer instance in a worker process.

    Parameters
    ----------
    job_id   : UUID string of the generation job.
    node     : Name of the pipeline node emitting the event
               (e.g. ``"strategy"``, ``"image_gen"``).
    progress : Integer 0–100 representing pipeline completion percentage.
    status   : One of ``"running"``, ``"complete"``, ``"failed"``.
    extra    : Optional dict of supplementary data (e.g. VRAM snapshot).
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning(
            "emit_progress: channel_layer is None — event not broadcast "
            "(job=%s node=%s)",
            job_id,
            node,
        )
        return

    await channel_layer.group_send(
        _group_name(job_id),
        {
            "type":      _EVENT_TYPE_DOT,   # dots → Channels routes to job_progress()
            "node":      node,
            "progress":  progress,
            "status":    status,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "extra":     extra or {},
        },
    )