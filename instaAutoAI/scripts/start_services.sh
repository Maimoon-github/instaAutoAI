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
