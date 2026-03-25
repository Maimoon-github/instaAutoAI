# #!/usr/bin/env bash
# set -e

# echo "Starting Ollama..."
# ollama serve &
# sleep 2

# echo "Starting Redis..."
# redis-server --daemonize yes

# echo "Starting ComfyUI..."
# cd ~/ComfyUI && python main.py --lowvram --fp8_e4m3fn &
# sleep 5

# echo "Starting Celery (concurrency=1)..."
# cd - > /dev/null
# celery -A config worker --concurrency=1 --loglevel=info &
# sleep 2

# echo "Starting Django ASGI server..."
# daphne config.asgi:application


































@echo off
setlocal enabledelayedexpansion

echo Starting InstaAutoAI Services...

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Check for required executables
where ollama >nul 2>&1 || (echo ollama not found in PATH & exit /b 1)
where redis-server >nul 2>&1 || (echo redis-server not found in PATH & exit /b 1)
where python >nul 2>&1 || (echo python not found in PATH & exit /b 1)
where celery >nul 2>&1 || (echo celery not found in PATH & exit /b 1)
where daphne >nul 2>&1 || (echo daphne not found in PATH & exit /b 1)

:: Start Ollama
echo Starting Ollama...
start /min "Ollama" cmd /c "ollama serve > logs\ollama.log 2>&1"
timeout /t 3 /nobreak >nul

:: Check Ollama (simple TCP check using PowerShell)
echo Waiting for Ollama...
:wait_ollama
powershell -Command "Test-NetConnection -ComputerName localhost -Port 11434 -InformationLevel Quiet" >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_ollama
)
echo Ollama ready.

:: Start Redis
echo Starting Redis...
start /min "Redis" cmd /c "redis-server --daemonize yes"
timeout /t 2 /nobreak >nul
:wait_redis
redis-cli ping >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_redis
)
echo Redis ready.

:: Start ComfyUI
echo Starting ComfyUI...
if defined COMFYUI_PATH (
    cd /d %COMFYUI_PATH%
) else (
    cd /d C:\ComfyUI
)
start /min "ComfyUI" cmd /c "python main.py --lowvram --fp8_e4m3fn > ..\logs\comfyui.log 2>&1"
cd /d %~dp0\..
timeout /t 5 /nobreak >nul
echo ComfyUI started (assuming port 8188).

:: Start Celery
echo Starting Celery worker (concurrency=1)...
start /min "Celery" cmd /c "celery -A config worker --concurrency=1 --loglevel=info > logs\celery.log 2>&1"
timeout /t 2 /nobreak >nul

:: Start Django ASGI server
echo Starting Django ASGI server (Daphne)...
start /min "Django" cmd /c "daphne -b 0.0.0.0 -p 8000 config.asgi:application > logs\daphne.log 2>&1"

echo All services started.
pause