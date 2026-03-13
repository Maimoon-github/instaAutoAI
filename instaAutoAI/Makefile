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
