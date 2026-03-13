JOB_STATUS_QUEUED  = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_DONE    = "done"
JOB_STATUS_FAILED  = "failed"

JOB_STATUS_CHOICES = [
    (JOB_STATUS_QUEUED,  "Queued"),
    (JOB_STATUS_RUNNING, "Running"),
    (JOB_STATUS_DONE,    "Done"),
    (JOB_STATUS_FAILED,  "Failed"),
]

VRAM_LOCK_KEY             = "instaAutoAI:vram_lock"
INSTAGRAM_CAPTION_MAX_CHARS = 2200
INSTAGRAM_HASHTAG_MAX     = 30
INSTAGRAM_HASHTAG_MIN     = 5
LLM_TOKEN_BUDGET          = 3500

ASPECT_RATIO_DIMENSIONS: dict = {
    "1:1": (1024, 1024),
    "4:5": (896,  1152),
    "9:16": (768,  1344),
}
