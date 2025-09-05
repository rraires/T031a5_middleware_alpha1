#!/bin/bash

# t031a5_middleware Deployment Script
# This script automates the deployment process for the middleware system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="t031a5_middleware"
DOCKER_IMAGE="${PROJECT_NAME}:latest"
CONTAINER_NAME="${PROJECT_NAME}_container"
CONFIG_FILE="config.json"
LOG_DIR="./logs"
DATA_DIR="./data"

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

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Python is installed (for local deployment)
    if ! command -v python3 &> /dev/null; then
        log_warning "Python 3 is not installed. Docker deployment only."
    fi
    
    log_success "Dependencies check completed"
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create necessary directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR/recordings"
    mkdir -p "$DATA_DIR/gestures"
    mkdir -p "./ssl"
    
    # Set permissions
    chmod 755 "$LOG_DIR"
    chmod 755 "$DATA_DIR"
    
    log_success "Directories setup completed"
}

generate_config() {
    log_info "Generating configuration files..."
    
    # Generate .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Environment Configuration
LOG_LEVEL=INFO
TZ=UTC
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_password_$(date +%s)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')
EOF
        log_success "Generated .env file"
    fi
    
    # Generate Redis configuration
    if [ ! -f "redis.conf" ]; then
        cat > redis.conf << EOF
# Redis Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF
        log_success "Generated redis.conf"
    fi
    
    # Generate Prometheus configuration
    if [ ! -f "prometheus.yml" ]; then
        cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 't031a5_middleware'
    static_configs:
      - targets: ['middleware:9090']
    scrape_interval: 5s
    metrics_path: '/metrics'
EOF
        log_success "Generated prometheus.yml"
    fi
    
    # Generate Nginx configuration
    if [ ! -f "nginx.conf" ]; then
        cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream middleware_api {
        server middleware:8000;
    }
    
    upstream web_dashboard {
        server web_dashboard:3000;
    }
    
    upstream grafana {
        server grafana:3000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location /api/ {
            proxy_pass http://middleware_api;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        location /ws {
            proxy_pass http://middleware:8001;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
        }
        
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host \$host;
        }
        
        location /health {
            proxy_pass http://middleware_api/api/v1/health;
        }
        
        location / {
            proxy_pass http://web_dashboard;
            proxy_set_header Host \$host;
        }
    }
}
EOF
        log_success "Generated nginx.conf"
    fi
}

build_docker_image() {
    log_info "Building Docker image..."
    
    # Build the Docker image
    docker build -t "$DOCKER_IMAGE" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        .
    
    log_success "Docker image built successfully"
}

run_tests() {
    log_info "Running tests..."
    
    # Run tests in Docker container
    docker build --target testing -t "${PROJECT_NAME}:test" .
    
    if docker run --rm "${PROJECT_NAME}:test"; then
        log_success "All tests passed"
    else
        log_error "Tests failed"
        exit 1
    fi
}

run_linting() {
    log_info "Running code quality checks..."
    
    # Run linting in Docker container
    docker build --target linting -t "${PROJECT_NAME}:lint" .
    
    if docker run --rm "${PROJECT_NAME}:lint"; then
        log_success "Code quality checks passed"
    else
        log_error "Code quality checks failed"
        exit 1
    fi
}

deploy_docker() {
    log_info "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Services deployed successfully"
        
        # Show service URLs
        echo ""
        log_info "Service URLs:"
        echo "  - API: http://localhost:8000"
        echo "  - WebSocket: ws://localhost:8001"
        echo "  - Web Dashboard: http://localhost:3001"
        echo "  - Grafana: http://localhost:3000"
        echo "  - Prometheus: http://localhost:9091"
        echo "  - Nginx Proxy: http://localhost:80"
    else
        log_error "Failed to start services"
        docker-compose logs
        exit 1
    fi
}

deploy_local() {
    log_info "Deploying locally..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e ".[dev]"
    
    # Run tests
    log_info "Running tests..."
    pytest tests/ -v
    
    # Start the middleware
    log_info "Starting middleware..."
    python main.py --config "$CONFIG_FILE" &
    MIDDLEWARE_PID=$!
    
    # Save PID for later cleanup
    echo $MIDDLEWARE_PID > middleware.pid
    
    log_success "Middleware started with PID: $MIDDLEWARE_PID"
    log_info "API available at: http://localhost:8000"
    log_info "WebSocket available at: ws://localhost:8001"
}

stop_services() {
    log_info "Stopping services..."
    
    # Stop Docker services
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
    fi
    
    # Stop local middleware
    if [ -f "middleware.pid" ]; then
        PID=$(cat middleware.pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            rm middleware.pid
            log_success "Local middleware stopped"
        fi
    fi
}

show_logs() {
    if [ -f "docker-compose.yml" ] && docker-compose ps | grep -q "Up"; then
        docker-compose logs -f
    else
        tail -f "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found"
    fi
}

show_status() {
    log_info "Service Status:"
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose ps
    fi
    
    if [ -f "middleware.pid" ]; then
        PID=$(cat middleware.pid)
        if kill -0 "$PID" 2>/dev/null; then
            echo "Local middleware: Running (PID: $PID)"
        else
            echo "Local middleware: Stopped"
        fi
    fi
}

show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup       Setup directories and configuration files"
    echo "  build       Build Docker image"
    echo "  test        Run tests"
    echo "  lint        Run code quality checks"
    echo "  deploy      Deploy with Docker Compose (default)"
    echo "  local       Deploy locally with Python"
    echo "  stop        Stop all services"
    echo "  logs        Show service logs"
    echo "  status      Show service status"
    echo "  clean       Clean up Docker images and containers"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup && $0 deploy    # Full deployment"
    echo "  $0 local                 # Local development"
    echo "  $0 test && $0 deploy     # Test then deploy"
}

clean_up() {
    log_info "Cleaning up..."
    
    # Stop services
    stop_services
    
    # Remove Docker containers and images
    docker-compose down --volumes --remove-orphans
    docker rmi "$DOCKER_IMAGE" 2>/dev/null || true
    docker rmi "${PROJECT_NAME}:test" 2>/dev/null || true
    docker rmi "${PROJECT_NAME}:lint" 2>/dev/null || true
    
    # Clean up build artifacts
    rm -rf build/ dist/ *.egg-info/
    
    log_success "Cleanup completed"
}

# Main script logic
case "${1:-deploy}" in
    setup)
        check_dependencies
        setup_directories
        generate_config
        ;;
    build)
        check_dependencies
        build_docker_image
        ;;
    test)
        check_dependencies
        run_tests
        ;;
    lint)
        check_dependencies
        run_linting
        ;;
    deploy)
        check_dependencies
        setup_directories
        generate_config
        build_docker_image
        deploy_docker
        ;;
    local)
        check_dependencies
        setup_directories
        deploy_local
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    clean)
        clean_up
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac