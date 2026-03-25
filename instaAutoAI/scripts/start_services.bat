@REM @echo off
@REM echo Starting InstaAutoAI Services...

@REM start "Ollama" cmd /k "ollama serve"
@REM timeout /t 3

@REM start "Redis" cmd /k "redis-server"
@REM timeout /t 2

@REM start "ComfyUI" cmd /k "cd /d C:\ComfyUI && python main.py --lowvram --fp8_e4m3fn"
@REM timeout /t 5

@REM start "Celery" cmd /k "celery -A config worker --concurrency=1 --loglevel=info"
@REM timeout /t 3

@REM start "Django" cmd /k "daphne config.asgi:application"

@REM echo All services started.
@REM pause

























#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create logs directory
mkdir -p logs

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local name=$3
    local max_attempts=30
    local attempt=0

    while ! nc -z "$host" "$port" 2>/dev/null; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            log_error "$name not ready after $max_attempts attempts"
            exit 1
        fi
        sleep 1
    done
    log_info "$name is ready"
}

# Ensure we are in the project root
cd "$(dirname "$0")/.." || exit 1

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
    log_info "Loaded .env"
fi

# Check for required executables
for cmd in ollama redis-server python celery daphne; do
    if ! command -v $cmd &> /dev/null; then
        log_error "$cmd not found in PATH"
        exit 1
    fi
done

# Start Ollama
log_info "Starting Ollama..."
ollama serve > logs/ollama.log 2>&1 &
OLLAMA_PID=$!
sleep 2

# Wait for Ollama API (default port 11434)
wait_for_service localhost 11434 "Ollama"

# Start Redis
log_info "Starting Redis..."
redis-server --daemonize yes
sleep 1
wait_for_service localhost 6379 "Redis"

# Start ComfyUI
log_info "Starting ComfyUI..."
cd "$COMFYUI_PATH" || log_warn "COMFYUI_PATH not set, using default ~/ComfyUI"
python main.py --lowvram --fp8_e4m3fn > ../logs/comfyui.log 2>&1 &
COMFYUI_PID=$!
cd - > /dev/null
sleep 5
# Optionally check ComfyUI health endpoint
wait_for_service localhost 8188 "ComfyUI"

# Start Celery worker
log_info "Starting Celery worker (concurrency=1)..."
celery -A config worker --concurrency=1 --loglevel=info > logs/celery.log 2>&1 &
CELERY_PID=$!
sleep 2

# Start Django ASGI server (Daphne)
log_info "Starting Django ASGI server (Daphne)..."
daphne -b 0.0.0.0 -p 8000 config.asgi:application > logs/daphne.log 2>&1 &
DAPHNE_PID=$!

# Trap SIGINT and SIGTERM to kill all background processes
trap 'kill $OLLAMA_PID $COMFYUI_PID $CELERY_PID $DAPHNE_PID 2>/dev/null; exit 0' INT TERM

log_info "All services started. Press Ctrl+C to stop."
wait