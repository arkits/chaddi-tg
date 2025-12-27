.PHONY: help install lint format test test-cov clean run docker-up docker-down docker-build docker-restart

# Default target
help:
	@echo "Available targets:"
	@echo "  make install      - Install dependencies"
	@echo "  make lint         - Check code with ruff"
	@echo "  make format       - Format code with ruff"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make clean        - Clean up generated files"
	@echo "  make run          - Run the application"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-restart - Restart Docker services"

# Install dependencies
install:
	uv sync

# Lint code
lint:
	uv run ruff check

# Format code
format:
	uv run ruff format

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	./test.sh

# Clean up generated files
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Run the application (user should run this manually)
run:
	@echo "Running application..."
	./run.sh

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-restart: docker-down docker-up

# Combined targets
check: lint test
	@echo "Lint and test checks passed!"

format-check: format lint
	@echo "Code formatted and linted!"

