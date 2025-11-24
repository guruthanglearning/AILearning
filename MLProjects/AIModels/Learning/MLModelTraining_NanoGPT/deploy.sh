#!/bin/bash

# TorchSharp Inspector Deployment Script
# This script builds and deploys the TorchSharp Inspector web application

set -e  # Exit on any error

echo "🚀 Starting TorchSharp Inspector Deployment..."

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
BUILD_CONFIG="Release"
SERVICES=("nanogpt-api" "nanogpt-dashboard" "torchsharp-inspector" "prometheus" "grafana")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check .NET SDK
    if ! command -v dotnet &> /dev/null; then
        log_error ".NET SDK is not installed or not in PATH"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build .NET applications
build_applications() {
    log_info "Building .NET applications..."
    
    # Build TorchSharp Inspector
    log_info "Building TorchSharp Inspector..."
    cd "$PROJECT_ROOT/TorchSharpInspector"
    dotnet build --configuration $BUILD_CONFIG --no-restore
    dotnet test ../TorchSharpInspector.Tests --configuration $BUILD_CONFIG --no-build --verbosity minimal
    
    # Build NanoGPT Dashboard
    log_info "Building NanoGPT Dashboard..."
    cd "$PROJECT_ROOT/NanoGpt.Dashboard"
    dotnet build --configuration $BUILD_CONFIG --no-restore
    
    # Build NanoGPT API
    log_info "Building NanoGPT API..."
    cd "$PROJECT_ROOT"
    dotnet build --configuration $BUILD_CONFIG --no-restore
    
    log_success "All applications built successfully"
}

# Restore NuGet packages
restore_packages() {
    log_info "Restoring NuGet packages..."
    cd "$PROJECT_ROOT"
    dotnet restore
    log_success "NuGet packages restored"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    cd "$PROJECT_ROOT"
    
    # Run TorchSharp Inspector tests
    if [ -d "TorchSharpInspector.Tests" ]; then
        log_info "Running TorchSharp Inspector tests..."
        dotnet test TorchSharpInspector.Tests --configuration $BUILD_CONFIG --logger "console;verbosity=minimal"
    fi
    
    log_success "Tests completed"
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"
    
    # Build with docker-compose
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    fi
    
    log_success "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    cd "$PROJECT_ROOT"
    
    # Stop existing services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    else
        docker compose -f "$DOCKER_COMPOSE_FILE" down
        docker compose -f "$DOCKER_COMPOSE_FILE" up -d
    fi
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=0
    local all_healthy=false
    
    while [ $attempt -lt $max_attempts ] && [ "$all_healthy" = false ]; do
        all_healthy=true
        
        for service in "${SERVICES[@]}"; do
            if command -v docker-compose &> /dev/null; then
                status=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q "$service" | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
            else
                status=$(docker compose -f "$DOCKER_COMPOSE_FILE" ps -q "$service" | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
            fi
            
            if [ "$status" != "healthy" ] && [ "$status" != "unknown" ]; then
                all_healthy=false
                break
            fi
        done
        
        if [ "$all_healthy" = false ]; then
            log_info "Waiting for services... (attempt $((attempt + 1))/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        log_success "All services are healthy"
    else
        log_warning "Some services may not be fully healthy yet"
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check API health
    if curl -f -s "http://localhost:8080/health" > /dev/null; then
        log_success "NanoGPT API is responding"
    else
        log_warning "NanoGPT API health check failed"
    fi
    
    # Check Dashboard
    if curl -f -s "http://localhost:5169" > /dev/null; then
        log_success "NanoGPT Dashboard is responding"
    else
        log_warning "NanoGPT Dashboard health check failed"
    fi
    
    # Check TorchSharp Inspector
    if curl -f -s "http://localhost:8082/api/health" > /dev/null; then
        log_success "TorchSharp Inspector is responding"
    else
        log_warning "TorchSharp Inspector health check failed"
    fi
    
    # Check Grafana
    if curl -f -s "http://localhost:3001" > /dev/null; then
        log_success "Grafana is responding"
    else
        log_warning "Grafana health check failed"
    fi
    
    # Check Prometheus
    if curl -f -s "http://localhost:9090" > /dev/null; then
        log_success "Prometheus is responding"
    else
        log_warning "Prometheus health check failed"
    fi
}

# Display service URLs
display_urls() {
    log_info "Deployment completed! Services are available at:"
    echo ""
    echo -e "${GREEN}🎭 NanoGPT Dashboard:${NC}     http://localhost:5169"
    echo -e "${BLUE}🔍 TorchSharp Inspector:${NC}  http://localhost:8082"
    echo -e "${YELLOW}📊 API Documentation:${NC}      http://localhost:8080/swagger"
    echo -e "${YELLOW}📊 Inspector API Docs:${NC}     http://localhost:8082/api-docs"
    echo -e "${GREEN}📈 Grafana Monitoring:${NC}    http://localhost:3001 (admin/admin123)"
    echo -e "${BLUE}📊 Prometheus Metrics:${NC}     http://localhost:9090"
    echo ""
    echo -e "${YELLOW}Health Checks:${NC}"
    echo -e "  • API Health:       http://localhost:8080/health"
    echo -e "  • Inspector Health: http://localhost:8082/api/health"
    echo ""
}

# Main deployment process
main() {
    log_info "TorchSharp Inspector Deployment Script v1.0.0"
    log_info "================================================"
    
    # Parse command line arguments
    SKIP_TESTS=false
    SKIP_BUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-tests   Skip running tests"
                echo "  --skip-build   Skip building applications"
                echo "  --help         Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    
    if [ "$SKIP_BUILD" = false ]; then
        restore_packages
        build_applications
        
        if [ "$SKIP_TESTS" = false ]; then
            run_tests
        fi
    fi
    
    build_docker_images
    deploy_services
    wait_for_services
    verify_deployment
    display_urls
    
    log_success "🎉 Deployment completed successfully!"
}

# Execute main function
main "$@"