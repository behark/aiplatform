#!/bin/bash

# Script to start only the backend service manually
echo "🚀 Starting Sovereign Agent Platform - Backend Only"

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

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs

# Start backend service
print_status "Starting backend service..."
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

# Start backend
print_status "Starting the backend service..."
python main.py
