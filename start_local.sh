#!/bin/bash

# Quick start script for local development and testing
# This script sets up the environment and runs the platform locally

set -e

echo "🚀 Starting Sovereign Agent Platform - Quick Setup"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs

# First attempt - try Docker Compose
print_status "Attempting to start both backend and frontend using Docker Compose..."
if docker-compose up -d; then
    print_success "✅ Both services are starting up!"
    print_success "🔹 Backend API will be available at: http://localhost:8000"
    print_success "🔹 Frontend WebUI will be available at: http://localhost:8080"
    print_warning "💡 Note: It may take a few moments for both services to fully initialize"

    print_status "To check logs, use:"
    echo "  - Backend logs: docker-compose logs -f sovereign-platform"
    echo "  - Frontend logs: docker-compose logs -f open-webui"
    echo ""
    print_status "To stop all services, run: docker-compose down"
else
    print_error "Docker Compose startup failed. This could be due to Docker not running or permission issues."
    print_warning "Falling back to starting services manually..."

    # Start backend service
    print_status "Starting backend service..."
    print_status "Setting up Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate

    print_status "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    print_status "Setting environment variables..."
    export PYTHONPATH=$PWD
    export OPENWEBUI_INTEGRATION=true
    export LOG_LEVEL=INFO

    # Start backend in background
    nohup python main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    print_success "Backend started with PID: $BACKEND_PID (logging to backend.log)"
    print_success "Backend API will be available at: http://localhost:8000"

    # Instructions for frontend
    print_status "To start the frontend WebUI separately, run:"
    echo "  1. Open a new terminal window"
    echo "  2. Navigate to the OpenWebUI directory if you have it installed locally"
    echo "  3. Or you can use the Docker image for OpenWebUI:"
    echo "     docker run -p 8080:8080 -e WEBUI_URL=http://0.0.0.0:8080 -e WEBUI_AUTH=false ghcr.io/open-webui/open-webui:main"

    print_warning "Remember to stop the backend when done by running: kill $BACKEND_PID"
fi
