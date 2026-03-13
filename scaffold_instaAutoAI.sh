#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# scaffold_instaAutoAI.sh
# Creates the full InstaAutoAI project file/folder hierarchy.
#
# Usage:
#   chmod +x scaffold_instaAutoAI.sh
#   ./scaffold_instaAutoAI.sh              # creates ./instaAutoAI/
#   ./scaffold_instaAutoAI.sh /my/path     # creates /my/path/instaAutoAI/
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Destination root ──────────────────────────────────────────────────────────
BASE="${1:-$(pwd)}/instaAutoAI"

if [[ -d "$BASE" ]]; then
  echo "⚠  Directory '$BASE' already exists. Aborting to avoid overwriting."
  exit 1
fi

echo "📁  Scaffolding InstaAutoAI at: $BASE"

# ── Helper: create a file and all parent dirs ─────────────────────────────────
mkf() {
  local path="$BASE/$1"
  mkdir -p "$(dirname "$path")"
  touch "$path"
}

# ─────────────────────────────────────────────────────────────────────────────
# ROOT FILES
# ─────────────────────────────────────────────────────────────────────────────
mkf "manage.py"
mkf ".env"
mkf ".env.example"
mkf ".gitignore"
mkf "requirements.txt"
mkf "requirements-dev.txt"
mkf "pyproject.toml"
mkf "README.md"
mkf "Makefile"

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG/
# ─────────────────────────────────────────────────────────────────────────────
mkf "config/__init__.py"
mkf "config/settings/__init__.py"
mkf "config/settings/base.py"
mkf "config/settings/development.py"
mkf "config/settings/production.py"
mkf "config/urls.py"
mkf "config/asgi.py"
mkf "config/wsgi.py"
mkf "config/celery.py"

# ─────────────────────────────────────────────────────────────────────────────
# APPS/JOBS/
# ─────────────────────────────────────────────────────────────────────────────
mkf "apps/jobs/__init__.py"
mkf "apps/jobs/admin.py"
mkf "apps/jobs/apps.py"
mkf "apps/jobs/consumers.py"
mkf "apps/jobs/models.py"
mkf "apps/jobs/routing.py"
mkf "apps/jobs/serializers.py"
mkf "apps/jobs/signals.py"
mkf "apps/jobs/tasks.py"
mkf "apps/jobs/urls.py"
mkf "apps/jobs/views.py"
mkf "apps/jobs/permissions.py"
mkf "apps/jobs/filters.py"
mkf "apps/jobs/pagination.py"
mkf "apps/jobs/exceptions.py"

mkf "apps/jobs/tests/__init__.py"
mkf "apps/jobs/tests/test_models.py"
mkf "apps/jobs/tests/test_views.py"
mkf "apps/jobs/tests/test_serializers.py"
mkf "apps/jobs/tests/test_consumers.py"
mkf "apps/jobs/tests/test_tasks.py"

mkf "apps/jobs/management/__init__.py"
mkf "apps/jobs/management/commands/__init__.py"
mkf "apps/jobs/management/commands/purge_old_jobs.py"
mkf "apps/jobs/management/commands/retry_failed_jobs.py"

# ─────────────────────────────────────────────────────────────────────────────
# APPS/PIPELINE/
# ─────────────────────────────────────────────────────────────────────────────
mkf "apps/pipeline/__init__.py"
mkf "apps/pipeline/apps.py"
mkf "apps/pipeline/state.py"
mkf "apps/pipeline/graph.py"
mkf "apps/pipeline/runner.py"
mkf "apps/pipeline/crew.py"
mkf "apps/pipeline/vram_manager.py"
mkf "apps/pipeline/llm_client.py"
mkf "apps/pipeline/exceptions.py"
mkf "apps/pipeline/health.py"

mkf "apps/pipeline/nodes/__init__.py"
mkf "apps/pipeline/nodes/base.py"
mkf "apps/pipeline/nodes/strategy.py"
mkf "apps/pipeline/nodes/visual_prompt.py"
mkf "apps/pipeline/nodes/image_gen.py"
mkf "apps/pipeline/nodes/video_gen.py"
mkf "apps/pipeline/nodes/caption.py"
mkf "apps/pipeline/nodes/hashtag.py"
mkf "apps/pipeline/nodes/export.py"

mkf "apps/pipeline/tests/__init__.py"
mkf "apps/pipeline/tests/test_graph.py"
mkf "apps/pipeline/tests/test_nodes.py"
mkf "apps/pipeline/tests/test_vram_manager.py"
mkf "apps/pipeline/tests/test_runner.py"

# ─────────────────────────────────────────────────────────────────────────────
# APPS/USERS/
# ─────────────────────────────────────────────────────────────────────────────
mkf "apps/users/__init__.py"
mkf "apps/users/admin.py"
mkf "apps/users/apps.py"
mkf "apps/users/models.py"
mkf "apps/users/serializers.py"
mkf "apps/users/urls.py"
mkf "apps/users/views.py"
mkf "apps/users/tests/__init__.py"
mkf "apps/users/tests/test_views.py"

# ─────────────────────────────────────────────────────────────────────────────
# CORE/
# ─────────────────────────────────────────────────────────────────────────────
mkf "core/__init__.py"
mkf "core/middleware.py"
mkf "core/mixins.py"
mkf "core/utils.py"
mkf "core/validators.py"
mkf "core/constants.py"
mkf "core/storages.py"

# ─────────────────────────────────────────────────────────────────────────────
# WORKFLOWS/
# ─────────────────────────────────────────────────────────────────────────────
mkf "workflows/ltx_i2v_portrait.json"

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATES/
# ─────────────────────────────────────────────────────────────────────────────
mkf "templates/base.html"
mkf "templates/dashboard.html"
mkf "templates/errors/404.html"
mkf "templates/errors/500.html"

# ─────────────────────────────────────────────────────────────────────────────
# STATIC/
# ─────────────────────────────────────────────────────────────────────────────
mkf "static/css/dashboard.css"
mkf "static/js/dashboard.js"
mkdir -p "$BASE/static/icons"

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME DIRECTORIES (gitkeep so they survive git clone)
# ─────────────────────────────────────────────────────────────────────────────
mkf "media/jobs/.gitkeep"
mkf "logs/.gitkeep"
mkf "checkpoints/.gitkeep"

# ─────────────────────────────────────────────────────────────────────────────
# SCRIPTS/
# ─────────────────────────────────────────────────────────────────────────────
mkf "scripts/start_services.bat"
mkf "scripts/start_services.sh"
mkf "scripts/seed_db.py"

# ─────────────────────────────────────────────────────────────────────────────
# DEPLOY/
# ─────────────────────────────────────────────────────────────────────────────
mkf "deploy/nginx.conf"
mkf "deploy/supervisord.conf"
mkf "deploy/Dockerfile"
mkf "deploy/docker-compose.yml"
mkf "deploy/.dockerignore"

# ─────────────────────────────────────────────────────────────────────────────
# SEED .gitignore
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/.gitignore" << 'EOF'
.env
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.venv/
venv/
media/
!media/jobs/.gitkeep
logs/*.log
!logs/.gitkeep
checkpoints/langgraph.sqlite
!checkpoints/.gitkeep
staticfiles/
*.DS_Store
.idea/
.vscode/
node_modules/
EOF

# ─────────────────────────────────────────────────────────────────────────────
# SEED .env.example
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/.env.example" << 'EOF'
# Django
SECRET_KEY=<your-secret-key-min-50-chars>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/instaAutoAI

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Media / Storage
MEDIA_ROOT=/absolute/path/to/instaAutoAI/media
MEDIA_URL=/media/

# Ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3:8b
OLLAMA_NUM_CTX=4096

# ComfyUI
COMFYUI_URL=http://localhost:8188
COMFYUI_OUTPUT_DIR=/absolute/path/to/ComfyUI/output

# LangGraph checkpoints
LANGGRAPH_CHECKPOINT_DB=checkpoints/langgraph.sqlite

# VRAM
VRAM_LOCK_TTL=3600
EOF

# ─────────────────────────────────────────────────────────────────────────────
# SEED Makefile
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/Makefile" << 'EOF'
.PHONY: run test migrate celery redis services lint format shell

run:
	daphne config.asgi:application

migrate:
	python manage.py migrate

test:
	pytest --cov=apps --cov-report=term-missing

celery:
	celery -A config worker --concurrency=1 --loglevel=info

redis:
	redis-server

services:
	ollama serve &
	redis-server &
	python ComfyUI/main.py --lowvram --fp8_e4m3fn &

lint:
	ruff check . && black --check .

format:
	black . && ruff check --fix .

shell:
	python manage.py shell_plus
EOF

# ─────────────────────────────────────────────────────────────────────────────
# SEED pyproject.toml
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/pyproject.toml" << 'EOF'
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
plugins = ["mypy_django_plugin.main"]
ignore_missing_imports = true

[tool.django-stubs]
django_settings_module = "config.settings.development"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.development"
asyncio_mode = "auto"
testpaths = ["apps"]
python_files = ["test_*.py"]
EOF

# ─────────────────────────────────────────────────────────────────────────────
# SEED manage.py
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/manage.py" << 'EOF'
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
EOF
chmod +x "$BASE/manage.py"

# ─────────────────────────────────────────────────────────────────────────────
# SEED config/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/config/__init__.py" << 'EOF'
from .celery import celery_app

__all__ = ("celery_app",)
EOF

# ─────────────────────────────────────────────────────────────────────────────
# SEED core/constants.py  (used by almost every other file)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/core/constants.py" << 'EOF'
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
EOF

# ─────────────────────────────────────────────────────────────────────────────
# SEED start_services.sh  (executable)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/scripts/start_services.sh" << 'EOF'
#!/usr/bin/env bash
set -e

echo "Starting Ollama..."
ollama serve &
sleep 2

echo "Starting Redis..."
redis-server --daemonize yes

echo "Starting ComfyUI..."
cd ~/ComfyUI && python main.py --lowvram --fp8_e4m3fn &
sleep 5

echo "Starting Celery (concurrency=1)..."
cd - > /dev/null
celery -A config worker --concurrency=1 --loglevel=info &
sleep 2

echo "Starting Django ASGI server..."
daphne config.asgi:application
EOF
chmod +x "$BASE/scripts/start_services.sh"

# ─────────────────────────────────────────────────────────────────────────────
# SEED start_services.bat  (Windows)
# ─────────────────────────────────────────────────────────────────────────────
cat > "$BASE/scripts/start_services.bat" << 'EOF'
@echo off
echo Starting InstaAutoAI Services...

start "Ollama" cmd /k "ollama serve"
timeout /t 3

start "Redis" cmd /k "redis-server"
timeout /t 2

start "ComfyUI" cmd /k "cd /d C:\ComfyUI && python main.py --lowvram --fp8_e4m3fn"
timeout /t 5

start "Celery" cmd /k "celery -A config worker --concurrency=1 --loglevel=info"
timeout /t 3

start "Django" cmd /k "daphne config.asgi:application"

echo All services started.
pause
EOF

# ─────────────────────────────────────────────────────────────────────────────
# DONE — print tree summary
# ─────────────────────────────────────────────────────────────────────────────
FILE_COUNT=$(find "$BASE" -type f | wc -l | tr -d ' ')
DIR_COUNT=$(find  "$BASE" -type d | wc -l | tr -d ' ')

echo ""
echo "✅  Done!"
echo "   Directories : $DIR_COUNT"
echo "   Files       : $FILE_COUNT"
echo "   Root        : $BASE"
echo ""
echo "Next steps:"
echo "  cd $BASE"
echo "  cp .env.example .env          # fill in your secrets"
echo "  python -m venv .venv && source .venv/bin/activate"
echo "  pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cu124"
echo "  python manage.py migrate"
echo "  ./scripts/start_services.sh   # or start_services.bat on Windows"
