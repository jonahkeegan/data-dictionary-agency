# Data Dictionary Agency (DDA) Makefile

.PHONY: help setup dev test lint format clean build docker-build docker-run

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON = python
PIP = pip
PYTEST = pytest
FLAKE8 = flake8
BLACK = black
ISORT = isort
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Help command
help:
	@echo "Data Dictionary Agency (DDA) Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup        Install dependencies"
	@echo "  make dev          Run development server"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linting"
	@echo "  make format       Format code"
	@echo "  make clean        Clean up build artifacts"
	@echo "  make build        Build the package"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-run   Run with Docker Compose"
	@echo "  make help         Show this help message"

# Install dependencies
setup:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

# Run development server
dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	$(PYTEST) -xvs tests/

# Run linting
lint:
	$(FLAKE8) src/ tests/

# Format code
format:
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build the package
build: clean
	$(PYTHON) setup.py sdist bdist_wheel

# Build Docker image
docker-build:
	$(DOCKER) build -t dda:latest .

# Run with Docker Compose
docker-run:
	$(DOCKER_COMPOSE) up
