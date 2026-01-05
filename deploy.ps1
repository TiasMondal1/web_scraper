# PowerShell deployment script for price tracker on Windows

Write-Host "Starting deployment..." -ForegroundColor Green

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    exit 1
}

# Check if docker-compose is installed
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Error: docker-compose is not installed" -ForegroundColor Red
    exit 1
}

# Build images
Write-Host "Building Docker images..." -ForegroundColor Yellow
docker-compose build

# Stop existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start containers
Write-Host "Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Show status
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "Container status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "Services are running:" -ForegroundColor Cyan
Write-Host "  Web Dashboard: http://localhost:5000"
Write-Host "  REST API: http://localhost:5001"


