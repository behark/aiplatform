#!/bin/bash

# Script to start both backend and frontend services together
echo "🚀 Starting Sovereign Agent Platform - Complete Setup"

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

# First check if Docker is running
print_status "Checking if Docker is running..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running or not installed. Please start Docker first."
    print_warning "Falling back to manual startup method..."
    USE_DOCKER=false
else
    print_success "Docker is running!"
    USE_DOCKER=true
fi

if [ "$USE_DOCKER" = true ]; then
    # Try Docker Compose
    print_status "Starting both backend and frontend using Docker Compose..."
    if docker-compose up -d; then
        print_success "✅ Both services are starting up in Docker containers!"
        print_success "🔹 Backend API will be available at: http://localhost:8000"
        print_success "🔹 Frontend WebUI will be available at: http://localhost:8080"
        print_warning "💡 Note: It may take a few moments for both services to fully initialize"

        print_status "To check logs, use:"
        echo "  - Backend logs: docker-compose logs -f sovereign-platform"
        echo "  - Frontend logs: docker-compose logs -f open-webui"
        echo ""
        print_status "To stop all services, run: docker-compose down"
        exit 0
    else
        print_error "Docker Compose startup failed. Falling back to manual startup method..."
        USE_DOCKER=false
    fi
fi

# If Docker startup failed or was skipped, start services manually
if [ "$USE_DOCKER" = false ]; then
    # Start backend service
    print_status "Setting up Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate

    print_status "Installing dependencies..."
    pip install --upgrade pip

    # Fix the pydantic dependency issue
    print_status "Fixing package compatibility issues..."
    pip uninstall -y pydantic pydantic-core
    pip install pydantic==2.5.2 pydantic-core==2.14.5

    # Now install the rest of the requirements
    pip install -r requirements.txt

    print_status "Setting environment variables..."
    export PYTHONPATH=$PWD
    export OPENWEBUI_INTEGRATION=true
    export LOG_LEVEL=INFO

    # Start backend in background
    print_status "Starting the backend service..."
    nohup python main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    print_success "Backend started with PID: $BACKEND_PID (logging to backend.log)"
    print_success "Backend API will be available at: http://localhost:8000"

    # Wait a bit for backend to initialize
    sleep 5

    # Start frontend (OpenWebUI)
    print_status "Starting the frontend service (OpenWebUI)..."

    # Try to use the Docker image for OpenWebUI if Docker is available
    if docker info > /dev/null 2>&1; then
        print_status "Starting OpenWebUI with Docker..."
        docker run -d --name open-webui -p 8080:8080 \
            -e WEBUI_URL=http://0.0.0.0:8080 \
            -e WEBUI_AUTH=false \
            -e API_BASE_URL=http://host.docker.internal:8000 \
            ghcr.io/open-webui/open-webui:main

        if [ $? -eq 0 ]; then
            print_success "Frontend started successfully!"
            print_success "Frontend WebUI will be available at: http://localhost:8080"
        else
            print_error "Failed to start OpenWebUI container."
            print_warning "You can start the frontend manually with:"
            echo "  docker run -p 8080:8080 -e WEBUI_URL=http://0.0.0.0:8080 -e WEBUI_AUTH=false -e API_BASE_URL=http://host.docker.internal:8000 ghcr.io/open-webui/open-webui:main"
        fi
    else
        print_warning "Docker is not available to start the frontend."
        print_warning "To start the frontend WebUI separately, follow these instructions:"
        echo "  1. Open a new terminal window"
        echo "  2. If you have OpenWebUI installed locally, navigate to that directory and start it"
        echo "  3. Make sure to configure it to connect to the backend at http://localhost:8000"
    fi

    print_warning "Remember to stop the services when done:"
    echo "  - To stop the backend: kill $BACKEND_PID"
    echo "  - To stop the frontend (if using Docker): docker stop open-webui && docker rm open-webui"
fi

print_success "Setup complete! Your Sovereign Agent Platform should now be running."
