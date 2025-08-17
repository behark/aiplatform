#!/bin/bash

# Quick start script for local development and testing
# This script sets up the environment and runs the platform locally

set -e

echo "🚀 Starting Sovereign Agent Platform - Quick Setup"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

print_status "Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

print_status "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

print_status "Creating necessary directories..."
mkdir -p data logs models config/secrets

print_status "Setting environment variables..."
export PYTHONPATH=$PWD
export OPENWEBUI_INTEGRATION=true
export LOG_LEVEL=INFO

print_status "Starting the Sovereign Agent Platform..."
echo ""
print_success "🎉 Platform is starting up!"
echo ""
echo "Your 7 Sovereign Agents:"
echo "1. 🧠 Advanced Consciousness Agent"
echo "2. 💾 Memory Core Agent"
echo "3. 🔄 Workflow Orchestration Agent"
echo "4. 🔍 Information Retrieval Agent"
echo "5. 📊 System Monitoring Agent"
echo "6. 🛡️ Governance & Audit Agent"
echo "7. ⚡ Data Pipeline Agent"
echo ""
print_status "Platform will be available at:"
echo "• Main API: http://localhost:8000"
echo "• Health Check: http://localhost:8000/health"
echo "• Agent Status: http://localhost:8000/agents"
echo "• API Docs: http://localhost:8000/docs"
echo ""

# Start the application
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
