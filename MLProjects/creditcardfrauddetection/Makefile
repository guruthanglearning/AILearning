# Makefile for Credit Card Fraud Detection System

# Variables
PYTHON = python
PYTEST = pytest
DOCKER = docker
DOCKER_COMPOSE = docker-compose -f docker-compose.prod.yml
PIP = pip

# Directories
APP_DIR = app
DATA_DIR = data
SCRIPTS_DIR = scripts
TESTS_DIR = tests

# Docker Configuration
DOCKER_IMAGE_API = fraud-detection-api
DOCKER_IMAGE_UI = fraud-detection-ui
DOCKER_NETWORK = fraud-detection-network

# Default target
.PHONY: help
help:
	@echo "==================================================="
	@echo "Credit Card Fraud Detection System - Makefile"
	@echo "==================================================="
	@echo ""
	@echo "Development Commands:"
	@echo "  setup              Setup development environment"
	@echo "  install            Install Python dependencies"
	@echo "  init-db            Initialize vector database"
	@echo "  test               Run all tests"
	@echo "  lint               Run code linting"
	@echo "  format             Format code with black and isort"
	@echo "  run-api            Run API development server"
	@echo "  run-ui             Run UI development server"
	@echo "  clean              Clean temporary files"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build       Build all Docker images"
	@echo "  docker-build-api   Build API Docker image only"
	@echo "  docker-build-ui    Build UI Docker image only"
	@echo "  docker-up          Start all Docker services"
	@echo "  docker-down        Stop all Docker services"
	@echo "  docker-restart     Restart Docker services"
	@echo "  docker-logs        View Docker logs"
	@echo "  docker-status      Check Docker service status"
	@echo "  docker-clean       Remove all Docker resources"
	@echo ""
	@echo "Utility Commands:"
	@echo "  backup             Backup Docker volumes"
	@echo "  restore            Restore Docker volumes"
	@echo "  health-check       Check service health"
	@echo ""

# ===========================================
# Development Commands
# ===========================================

# Setup development environment
.PHONY: setup
setup: install init-db
	@echo "✅ Development environment setup complete"

# Install dependencies
.PHONY: install
install:
	@echo "📦 Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

# Initialize vector database
.PHONY: init-db
init-db:
	@echo "🔧 Initializing vector database..."
	$(PYTHON) $(SCRIPTS_DIR)/init_vector_db.py
	@echo "✅ Vector database initialized"

# Run tests
.PHONY: test
test:
	@echo "🧪 Running tests..."
	$(PYTEST) $(TESTS_DIR) -v --cov=$(APP_DIR)
	@echo "✅ Tests complete"

# Run linting
.PHONY: lint
lint:
	@echo "🔍 Running linters..."
	flake8 $(APP_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	mypy $(APP_DIR) $(SCRIPTS_DIR)
	@echo "✅ Linting complete"

# Format code
.PHONY: format
format:
	@echo "🎨 Formatting code..."
	black $(APP_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	isort $(APP_DIR) $(SCRIPTS_DIR) $(TESTS_DIR)
	@echo "✅ Code formatted"

# Run API development server
.PHONY: run-api
run-api:
	@echo "🚀 Starting API development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run UI development server
.PHONY: run-ui
run-ui:
	@echo "🚀 Starting UI development server..."
	cd ui && streamlit run app.py --server.port 8501

# Clean temporary files
.PHONY: clean
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache htmlcov .mypy_cache
	@echo "✅ Cleanup complete"

# ===========================================
# Docker Commands
# ===========================================

# Build all Docker images
.PHONY: docker-build
docker-build:
	@echo "🐳 Building Docker images..."
	$(DOCKER_COMPOSE) build --no-cache
	@echo "✅ Docker images built"

# Build API Docker image
.PHONY: docker-build-api
docker-build-api:
	@echo "🐳 Building API Docker image..."
	$(DOCKER) build -f Dockerfile.api -t $(DOCKER_IMAGE_API):latest .
	@echo "✅ API image built"

# Build UI Docker image
.PHONY: docker-build-ui
docker-build-ui:
	@echo "🐳 Building UI Docker image..."
	$(DOCKER) build -f Dockerfile.ui -t $(DOCKER_IMAGE_UI):latest .
	@echo "✅ UI image built"

# Start Docker services
.PHONY: docker-up
docker-up:
	@echo "🚀 Starting Docker services..."
	$(DOCKER_COMPOSE) up -d
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 10
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Access URLs:"
	@echo "   - API Server: http://localhost:8000"
	@echo "   - API Docs: http://localhost:8000/docs"
	@echo "   - UI Dashboard: http://localhost:8501"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana: http://localhost:3000"

# Stop Docker services
.PHONY: docker-down
docker-down:
	@echo "🛑 Stopping Docker services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Services stopped"

# Restart Docker services
.PHONY: docker-restart
docker-restart:
	@echo "🔄 Restarting Docker services..."
	$(DOCKER_COMPOSE) restart
	@echo "✅ Services restarted"

# View Docker logs
.PHONY: docker-logs
docker-logs:
	@echo "📋 Showing Docker logs (Ctrl+C to exit)..."
	$(DOCKER_COMPOSE) logs -f

# Check Docker service status
.PHONY: docker-status
docker-status:
	@echo "📊 Docker Service Status:"
	$(DOCKER_COMPOSE) ps

# Clean Docker resources
.PHONY: docker-clean
docker-clean:
	@echo "⚠️  This will remove all Docker containers, volumes, and images."
	@echo "Press Ctrl+C to cancel, or press Enter to continue..."
	@read dummy
	@echo "🧹 Cleaning Docker resources..."
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "✅ Docker cleanup complete"

# ===========================================
# Utility Commands
# ===========================================

# Backup Docker volumes
.PHONY: backup
backup:
	@echo "💾 Backing up Docker volumes..."
	@mkdir -p backups
	$(DOCKER) run --rm -v fraud-detection_model-data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/models-$(shell date +%Y%m%d-%H%M%S).tar.gz /data
	$(DOCKER) run --rm -v fraud-detection_chroma-data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/chroma-$(shell date +%Y%m%d-%H%M%S).tar.gz /data
	@echo "✅ Backup complete - saved to backups/ directory"

# Restore Docker volumes
.PHONY: restore
restore:
	@echo "📥 Restoring Docker volumes..."
	@echo "Available backups:"
	@ls -la backups/*.tar.gz
	@echo "Enter backup filename (e.g., models-20260102-120000.tar.gz):"
	@read backup_file && \
	$(DOCKER) run --rm -v fraud-detection_model-data:/data -v $(PWD)/backups:/backup alpine tar xzf /backup/$$backup_file -C /
	@echo "✅ Restore complete"

# Health check
.PHONY: health-check
health-check:
	@echo "🏥 Checking service health..."
	@echo "API Health:"
	@curl -sf http://localhost:8000/health && echo "  ✅ API is healthy" || echo "  ❌ API is not responding"
	@echo "UI Health:"
	@curl -sf http://localhost:8501/_stcore/health && echo "  ✅ UI is healthy" || echo "  ❌ UI is not responding"
	@echo "Prometheus:"
	@curl -sf http://localhost:9090/-/healthy && echo "  ✅ Prometheus is healthy" || echo "  ❌ Prometheus is not responding"
	@echo "Grafana:"
	@curl -sf http://localhost:3000/api/health && echo "  ✅ Grafana is healthy" || echo "  ❌ Grafana is not responding"

# ===========================================
# Quick Commands
# ===========================================

# Full deployment
.PHONY: deploy
deploy: docker-build docker-up health-check
	@echo "🎉 Deployment complete!"

# Development mode
.PHONY: dev
dev: install
	@echo "🚀 Starting development servers..."
	@echo "Run 'make run-api' in one terminal and 'make run-ui' in another"


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
