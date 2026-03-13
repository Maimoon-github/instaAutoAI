"""
Centralized constants for the entire project.
"""

# -----------------------------------------------------------------------------
# Job Status
# -----------------------------------------------------------------------------
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_DONE = "done"
JOB_STATUS_FAILED = "failed"

JOB_STATUS_CHOICES = [
    (JOB_STATUS_QUEUED, "Queued"),
    (JOB_STATUS_RUNNING, "Running"),
    (JOB_STATUS_DONE, "Done"),
    (JOB_STATUS_FAILED, "Failed"),
]

# -----------------------------------------------------------------------------
# Agent Types (used in CrewAI)
# -----------------------------------------------------------------------------
AGENT_TYPE_STRATEGIST = "strategist"
AGENT_TYPE_VISUAL_DIRECTOR = "visual_director"
AGENT_TYPE_COPYWRITER = "copywriter"
AGENT_TYPE_HASHTAG_SPECIALIST = "hashtag_specialist"
AGENT_TYPE_IMAGE_GENERATOR = "image_generator"
AGENT_TYPE_VIDEO_GENERATOR = "video_generator"

AGENT_TYPE_CHOICES = [
    (AGENT_TYPE_STRATEGIST, "Strategist"),
    (AGENT_TYPE_VISUAL_DIRECTOR, "Visual Director"),
    (AGENT_TYPE_COPYWRITER, "Copywriter"),
    (AGENT_TYPE_HASHTAG_SPECIALIST, "Hashtag Specialist"),
    (AGENT_TYPE_IMAGE_GENERATOR, "Image Generator"),
    (AGENT_TYPE_VIDEO_GENERATOR, "Video Generator"),
]

# -----------------------------------------------------------------------------
# Instagram Limits
# -----------------------------------------------------------------------------
INSTAGRAM_CAPTION_MAX_CHARS = 2200
INSTAGRAM_HASHTAG_MAX = 30
INSTAGRAM_HASHTAG_MIN = 5

# -----------------------------------------------------------------------------
# LLM / Agent Configuration
# -----------------------------------------------------------------------------
LLM_TOKEN_BUDGET = 3500  # default token budget per agent call
VRAM_LOCK_KEY = "instaAutoAI:vram_lock"

# VRAM thresholds (in bytes)
VRAM_8GB = 8 * 1024**3  # ~8.59e9 bytes
VRAM_7_8GB = int(7.8 * 1024**3)  # ~8.37e9 bytes
VRAM_5_6GB = int(5.6 * 1024**3)  # ~6.01e9 bytes

# -----------------------------------------------------------------------------
# Aspect Ratios and Dimensions
# -----------------------------------------------------------------------------
ASPECT_RATIO_DIMENSIONS = {
    "1:1": (1024, 1024),
    "4:5": (896, 1152),
    "9:16": (768, 1344),
}

ALLOWED_ASPECT_RATIOS = list(ASPECT_RATIO_DIMENSIONS.keys())

# -----------------------------------------------------------------------------
# Pagination
# -----------------------------------------------------------------------------
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# -----------------------------------------------------------------------------
# Regular Expressions
# -----------------------------------------------------------------------------
HASHTAG_REGEX = r"^#[a-zA-Z0-9_]+$"  # simple hashtag validation
USERNAME_REGEX = r"^[a-zA-Z0-9_]{3,30}$"

# -----------------------------------------------------------------------------
# HTTP Status Codes (optional, Django's HttpResponse already has constants)
# -----------------------------------------------------------------------------
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500

# -----------------------------------------------------------------------------
# Cache Timeouts (in seconds)
# -----------------------------------------------------------------------------
CACHE_1_MINUTE = 60
CACHE_5_MINUTES = 300
CACHE_1_HOUR = 3600
CACHE_1_DAY = 86400