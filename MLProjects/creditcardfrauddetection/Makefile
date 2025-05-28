# Makefile for Credit Card Fraud Detection System

# Variables
PYTHON = python
PYTEST = pytest
DOCKER = docker
DOCKER_COMPOSE = docker-compose
PIP = pip

# Directories
APP_DIR = app
DATA_DIR = data
SCRIPTS_DIR = scripts
TESTS_DIR = tests

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  setup           Setup development environment"
	@echo "  install         Install dependencies"
	@echo "  init-db         Initialize vector database"
	@echo "  test            Run tests"
	@echo "  lint            Run linting"
	@echo "  format          Format code"
	@echo "  run             Run development server"
	@echo "  docker-build    Build Docker image"
	@echo "  docker-run      Run using Docker"
	@echo "  docker-compose  Run using Docker Compose"
	@echo "  clean           Clean temporary files"

# Setup development environment
.PHONY: setup
setup: install init-db
	@echo "Development environment setup complete"

# Install dependencies
.PHONY: install
install:
	$(PIP) install -r requirements.txt

# Initialize vector database
.PHONY: init-db
init-db:
	$(PYTHON) $(SCRIPTS_DIR)/init_vector_db.py

# Run tests
.PHONY: test
test:
	$(PYTEST) $(TESTS_DIR) -v --cov=$(APP_DIR)

# Run linting
.PHONY: lint
lint:
	flake8 $(APP_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	mypy $(APP_DIR) $(SCRIPTS_DIR)

# Format code
.PHONY: format
format:
	black $(APP_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	isort $(APP_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)

# Run development server
.PHONY: run
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Build Docker image
.PHONY: docker-build
docker-build:
	$(DOCKER) build -t fraud-detection-api .

# Run using Docker
.PHONY: docker-run
docker-run:
	$(DOCKER) run -p 8000:8000 --env-file .env fraud-detection-api

# Run using Docker Compose
.PHONY: docker-compose
docker-compose:
	$(DOCKER_COMPOSE) up -d

# Stop Docker Compose
.PHONY: docker-stop
docker-stop:
	$(DOCKER_COMPOSE) down

# Clean temporary files
.PHONY: clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type f -name "*.bak" -delete
	find . -type f -name "*.log" -delete
