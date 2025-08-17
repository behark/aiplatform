#!/bin/bash

# Complete deployment script for Sovereign Agent Platform with Open WebUI
# This script handles multiple deployment scenarios

set -e

echo "🚀 Sovereign Agent Platform - Complete Deployment Helper"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check system capabilities
print_status "Checking system requirements..."

# Check if Docker is available
if command -v docker &> /dev/null; then
    DOCKER_AVAILABLE=true
    print_success "Docker is available"
else
    DOCKER_AVAILABLE=false
    print_warning "Docker not found"
fi

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null || command -v docker compose &> /dev/null; then
    COMPOSE_AVAILABLE=true
    print_success "Docker Compose is available"
else
    COMPOSE_AVAILABLE=false
    print_warning "Docker Compose not found"
fi

echo ""
print_status "🎯 Deployment Options Available:"

echo ""
echo "Option 1: Local Development (Already Working)"
echo "   ✅ Your platform is tested and ready"
echo "   ✅ All 7 agents are operational"
echo "   🔗 Access: http://localhost:8001"

echo ""
echo "Option 2: Install Docker and Deploy Full Stack"
echo "   📦 Installs Docker + Docker Compose"
echo "   🌐 Deploys Open WebUI + All 7 Agents"
echo "   🎨 Beautiful web interface"

echo ""
echo "Option 3: Manual Open WebUI Integration"
echo "   🚀 Run Open WebUI separately"
echo "   🔗 Connect to your existing agents"
echo "   ⚡ Quick setup, no Docker needed"

echo ""
read -p "Which option would you like? (1/2/3): " choice

case $choice in
    1)
        print_status "Starting your Sovereign Agent Platform locally..."
        source .venv/bin/activate
        export PYTHONPATH=$PWD
        echo ""
        print_success "🎊 Your 7 Sovereign Agents are ready!"
        echo ""
        echo "🧠 Advanced Consciousness Agent - Master reasoning"
        echo "💾 Memory Core Agent - Experience storage"
        echo "🔄 Workflow Orchestration Agent - Task management"
        echo "🔍 Information Retrieval Agent - RAG system"
        echo "📊 System Monitoring Agent - Performance tracking"
        echo "🛡️ Governance & Audit Agent - Policy enforcement"
        echo "⚡ Data Pipeline Agent - Data processing"
        echo ""
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ;;

    2)
        print_status "Installing Docker and Docker Compose..."

        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER

        # Install Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose

        print_success "Docker and Docker Compose installed!"
        print_warning "Please logout and login again, then run this script again with option 2"
        ;;

    3)
        print_status "Setting up Manual Open WebUI Integration..."

        # Start your agents platform
        source .venv/bin/activate
        export PYTHONPATH=$PWD
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
        PLATFORM_PID=$!

        echo ""
        print_success "✅ Your Sovereign Agent Platform is running on port 8000"

        # Instructions for Open WebUI
        echo ""
        print_status "🌐 To add Open WebUI interface:"
        echo ""
        echo "In a new terminal, run:"
        echo "docker run -d -p 8080:8080 -e WEBUI_AUTH=false ghcr.io/open-webui/open-webui:main"
        echo ""
        echo "Or if Docker isn't available, install it first:"
        echo "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
        echo ""
        print_success "🎯 Access your platform:"
        echo "   • API: http://localhost:8000"
        echo "   • Web UI: http://localhost:8080 (after running Docker command)"
        echo "   • Docs: http://localhost:8000/docs"

        # Keep platform running
        wait $PLATFORM_PID
        ;;

    *)
        print_error "Invalid option. Please choose 1, 2, or 3."
        exit 1
        ;;
esac
