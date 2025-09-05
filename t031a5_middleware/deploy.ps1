# t031a5_middleware Deployment Script for Windows PowerShell
# This script automates the deployment process for the middleware system on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet('setup', 'build', 'test', 'lint', 'deploy', 'local', 'stop', 'logs', 'status', 'clean', 'help')]
    [string]$Command = 'deploy'
)

# Configuration
$ProjectName = "t031a5_middleware"
$DockerImage = "${ProjectName}:latest"
$ContainerName = "${ProjectName}_container"
$ConfigFile = "config.json"
$LogDir = "./logs"
$DataDir = "./data"

# Colors for output
$Colors = @{
    Red = 'Red'
    Green = 'Green'
    Yellow = 'Yellow'
    Blue = 'Blue'
    White = 'White'
}

# Functions
function Write-LogInfo {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-LogWarning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Test-Dependencies {
    Write-LogInfo "Checking dependencies..."
    
    # Check if Docker is installed
    try {
        $dockerVersion = docker --version
        Write-LogInfo "Docker found: $dockerVersion"
    }
    catch {
        Write-LogError "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check if Docker Compose is installed
    try {
        $composeVersion = docker-compose --version
        Write-LogInfo "Docker Compose found: $composeVersion"
    }
    catch {
        Write-LogError "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    # Check if Python is installed (for local deployment)
    try {
        $pythonVersion = python --version
        Write-LogInfo "Python found: $pythonVersion"
    }
    catch {
        Write-LogWarning "Python is not installed. Docker deployment only."
    }
    
    Write-LogSuccess "Dependencies check completed"
}

function Initialize-Directories {
    Write-LogInfo "Setting up directories..."
    
    # Create necessary directories
    $directories = @(
        $LogDir,
        "$DataDir/recordings",
        "$DataDir/gestures",
        "./ssl"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-LogInfo "Created directory: $dir"
        }
    }
    
    Write-LogSuccess "Directories setup completed"
}

function New-ConfigurationFiles {
    Write-LogInfo "Generating configuration files..."
    
    # Generate .env file if it doesn't exist
    if (!(Test-Path ".env")) {
        $envContent = @"
# Environment Configuration
LOG_LEVEL=INFO
TZ=UTC
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_password_$(Get-Date -Format 'yyyyMMddHHmmss')
BUILD_DATE=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
VCS_REF=$(try { git rev-parse --short HEAD } catch { 'unknown' })
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-LogSuccess "Generated .env file"
    }
    
    # Generate Redis configuration
    if (!(Test-Path "redis.conf")) {
        $redisContent = @"
# Redis Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
"@
        $redisContent | Out-File -FilePath "redis.conf" -Encoding UTF8
        Write-LogSuccess "Generated redis.conf"
    }
    
    # Generate Prometheus configuration
    if (!(Test-Path "prometheus.yml")) {
        $prometheusContent = @"
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
"@
        $prometheusContent | Out-File -FilePath "prometheus.yml" -Encoding UTF8
        Write-LogSuccess "Generated prometheus.yml"
    }
    
    # Generate Nginx configuration
    if (!(Test-Path "nginx.conf")) {
        $nginxContent = @"
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
            proxy_set_header Host `$host;
            proxy_set_header X-Real-IP `$remote_addr;
            proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        }
        
        location /ws {
            proxy_pass http://middleware:8001;
            proxy_http_version 1.1;
            proxy_set_header Upgrade `$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host `$host;
        }
        
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host `$host;
        }
        
        location /health {
            proxy_pass http://middleware_api/api/v1/health;
        }
        
        location / {
            proxy_pass http://web_dashboard;
            proxy_set_header Host `$host;
        }
    }
}
"@
        $nginxContent | Out-File -FilePath "nginx.conf" -Encoding UTF8
        Write-LogSuccess "Generated nginx.conf"
    }
}

function Build-DockerImage {
    Write-LogInfo "Building Docker image..."
    
    $buildDate = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ'
    $vcsRef = try { git rev-parse --short HEAD } catch { 'unknown' }
    
    # Build the Docker image
    docker build -t $DockerImage `
        --build-arg BUILD_DATE=$buildDate `
        --build-arg VCS_REF=$vcsRef `
        .
    
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Docker image built successfully"
    } else {
        Write-LogError "Failed to build Docker image"
        exit 1
    }
}

function Invoke-Tests {
    Write-LogInfo "Running tests..."
    
    # Build test image
    docker build --target testing -t "${ProjectName}:test" .
    
    if ($LASTEXITCODE -eq 0) {
        # Run tests in Docker container
        docker run --rm "${ProjectName}:test"
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "All tests passed"
        } else {
            Write-LogError "Tests failed"
            exit 1
        }
    } else {
        Write-LogError "Failed to build test image"
        exit 1
    }
}

function Invoke-Linting {
    Write-LogInfo "Running code quality checks..."
    
    # Build linting image
    docker build --target linting -t "${ProjectName}:lint" .
    
    if ($LASTEXITCODE -eq 0) {
        # Run linting in Docker container
        docker run --rm "${ProjectName}:lint"
        
        if ($LASTEXITCODE -eq 0) {
            Write-LogSuccess "Code quality checks passed"
        } else {
            Write-LogError "Code quality checks failed"
            exit 1
        }
    } else {
        Write-LogError "Failed to build linting image"
        exit 1
    }
}

function Start-DockerDeployment {
    Write-LogInfo "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Start services
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        # Wait for services to be ready
        Write-LogInfo "Waiting for services to start..."
        Start-Sleep -Seconds 30
        
        # Check if services are running
        $runningServices = docker-compose ps --filter "status=running"
        
        if ($runningServices) {
            Write-LogSuccess "Services deployed successfully"
            
            # Show service URLs
            Write-Host ""
            Write-LogInfo "Service URLs:"
            Write-Host "  - API: http://localhost:8000"
            Write-Host "  - WebSocket: ws://localhost:8001"
            Write-Host "  - Web Dashboard: http://localhost:3001"
            Write-Host "  - Grafana: http://localhost:3000"
            Write-Host "  - Prometheus: http://localhost:9091"
            Write-Host "  - Nginx Proxy: http://localhost:80"
        } else {
            Write-LogError "Failed to start services"
            docker-compose logs
            exit 1
        }
    } else {
        Write-LogError "Failed to start Docker Compose services"
        exit 1
    }
}

function Start-LocalDeployment {
    Write-LogInfo "Deploying locally..."
    
    # Check if virtual environment exists
    if (!(Test-Path "venv")) {
        Write-LogInfo "Creating virtual environment..."
        python -m venv venv
    }
    
    # Activate virtual environment
    & ".\venv\Scripts\Activate.ps1"
    
    # Install dependencies
    Write-LogInfo "Installing dependencies..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e ".[dev]"
    
    if ($LASTEXITCODE -eq 0) {
        # Run tests
        Write-LogInfo "Running tests..."
        pytest tests/ -v
        
        if ($LASTEXITCODE -eq 0) {
            # Start the middleware
            Write-LogInfo "Starting middleware..."
            $process = Start-Process -FilePath "python" -ArgumentList "main.py", "--config", $ConfigFile -PassThru -NoNewWindow
            
            # Save PID for later cleanup
            $process.Id | Out-File -FilePath "middleware.pid" -Encoding UTF8
            
            Write-LogSuccess "Middleware started with PID: $($process.Id)"
            Write-LogInfo "API available at: http://localhost:8000"
            Write-LogInfo "WebSocket available at: ws://localhost:8001"
        } else {
            Write-LogError "Tests failed"
            exit 1
        }
    } else {
        Write-LogError "Failed to install dependencies"
        exit 1
    }
}

function Stop-Services {
    Write-LogInfo "Stopping services..."
    
    # Stop Docker services
    if (Test-Path "docker-compose.yml") {
        docker-compose down
    }
    
    # Stop local middleware
    if (Test-Path "middleware.pid") {
        $pid = Get-Content "middleware.pid" -Raw
        $pid = $pid.Trim()
        
        try {
            $process = Get-Process -Id $pid -ErrorAction Stop
            Stop-Process -Id $pid -Force
            Remove-Item "middleware.pid"
            Write-LogSuccess "Local middleware stopped"
        }
        catch {
            Write-LogWarning "Middleware process not found or already stopped"
            Remove-Item "middleware.pid" -ErrorAction SilentlyContinue
        }
    }
}

function Show-Logs {
    if ((Test-Path "docker-compose.yml") -and (docker-compose ps --filter "status=running")) {
        docker-compose logs -f
    } else {
        $logFiles = Get-ChildItem -Path $LogDir -Filter "*.log" -ErrorAction SilentlyContinue
        if ($logFiles) {
            Get-Content $logFiles.FullName -Wait
        } else {
            Write-LogWarning "No log files found"
        }
    }
}

function Show-Status {
    Write-LogInfo "Service Status:"
    
    if (Test-Path "docker-compose.yml") {
        docker-compose ps
    }
    
    if (Test-Path "middleware.pid") {
        $pid = Get-Content "middleware.pid" -Raw
        $pid = $pid.Trim()
        
        try {
            $process = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "Local middleware: Running (PID: $pid)"
        }
        catch {
            Write-Host "Local middleware: Stopped"
        }
    }
}

function Remove-Cleanup {
    Write-LogInfo "Cleaning up..."
    
    # Stop services
    Stop-Services
    
    # Remove Docker containers and images
    docker-compose down --volumes --remove-orphans
    docker rmi $DockerImage -f 2>$null
    docker rmi "${ProjectName}:test" -f 2>$null
    docker rmi "${ProjectName}:lint" -f 2>$null
    
    # Clean up build artifacts
    Remove-Item -Path "build", "dist", "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-LogSuccess "Cleanup completed"
}

function Show-Help {
    Write-Host "Usage: .\deploy.ps1 [COMMAND]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  setup       Setup directories and configuration files"
    Write-Host "  build       Build Docker image"
    Write-Host "  test        Run tests"
    Write-Host "  lint        Run code quality checks"
    Write-Host "  deploy      Deploy with Docker Compose (default)"
    Write-Host "  local       Deploy locally with Python"
    Write-Host "  stop        Stop all services"
    Write-Host "  logs        Show service logs"
    Write-Host "  status      Show service status"
    Write-Host "  clean       Clean up Docker images and containers"
    Write-Host "  help        Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1 setup; .\deploy.ps1 deploy    # Full deployment"
    Write-Host "  .\deploy.ps1 local                        # Local development"
    Write-Host "  .\deploy.ps1 test; .\deploy.ps1 deploy     # Test then deploy"
}

# Main script logic
try {
    switch ($Command) {
        'setup' {
            Test-Dependencies
            Initialize-Directories
            New-ConfigurationFiles
        }
        'build' {
            Test-Dependencies
            Build-DockerImage
        }
        'test' {
            Test-Dependencies
            Invoke-Tests
        }
        'lint' {
            Test-Dependencies
            Invoke-Linting
        }
        'deploy' {
            Test-Dependencies
            Initialize-Directories
            New-ConfigurationFiles
            Build-DockerImage
            Start-DockerDeployment
        }
        'local' {
            Test-Dependencies
            Initialize-Directories
            Start-LocalDeployment
        }
        'stop' {
            Stop-Services
        }
        'logs' {
            Show-Logs
        }
        'status' {
            Show-Status
        }
        'clean' {
            Remove-Cleanup
        }
        'help' {
            Show-Help
        }
        default {
            Write-LogError "Unknown command: $Command"
            Show-Help
            exit 1
        }
    }
}
catch {
    Write-LogError "An error occurred: $($_.Exception.Message)"
    exit 1
}

Write-LogSuccess "Operation completed successfully"