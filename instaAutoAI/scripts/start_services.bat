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
