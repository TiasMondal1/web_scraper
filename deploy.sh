#!/bin/bash
# Deployment script for price tracker

set -e

echo "Starting deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Build images
echo "Building Docker images..."
docker-compose build

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Start containers
echo "Starting containers..."
docker-compose up -d

# Show status
echo "Deployment completed!"
echo "Container status:"
docker-compose ps

echo ""
echo "Services are running:"
echo "  Web Dashboard: http://localhost:5000"
echo "  REST API: http://localhost:5001"

