.PHONY: help install install-dev test lint clean

help:
	@echo "Available commands:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install development dependencies (includes dev tools)"
	@echo "  make test         Run tests with pytest"
	@echo "  make lint         Run linting (black, ruff, mypy)"
	@echo "  make clean        Remove cache files, .env, and temporary assets"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest

lint:
	black --check .
	ruff check .
	mypy .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -f .env
	rm -rf checkpoints/ media/ staticfiles/