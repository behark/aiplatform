#!/bin/bash

# Railway Frontend Deployment Script
# This script deploys your Sovereign Agent Platform with a beautiful frontend interface

echo "🚀 Deploying Sovereign Agent Platform with Frontend Interface to Railway..."
echo "================================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    print_error "Railway CLI not found. Installing..."
    
    # Install Railway CLI
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install railway
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://railway.app/install.sh | sh
    else
        print_error "Please install Railway CLI manually: https://docs.railway.app/quick-start"
        exit 1
    fi
fi

print_status "Railway CLI found ✅"

# Login to Railway (if not already logged in)
if ! railway whoami &> /dev/null; then
    print_status "Please log in to Railway..."
    railway login
fi

print_success "Logged in to Railway ✅"

# Set up the frontend deployment configuration
print_status "Setting up frontend configuration..."

# Copy the frontend railway config
cp railway-frontend.json railway.json

print_status "Building and deploying your Sovereign Agent Platform..."

# Deploy to Railway
if railway up --detach; then
    print_success "🎉 Deployment successful!"
    
    # Generate a domain
    print_status "Generating public domain..."
    railway domain generate
    
    # Get the domain
    DOMAIN=$(railway domain | grep -o 'https://[^"]*' | head -1)
    
    echo ""
    print_success "🌐 Your Sovereign Agent Platform is now live!"
    echo ""
    echo "🔗 Public URL: $DOMAIN"
    echo ""
    print_status "🤖 Available Features:"
    echo "   • 🧠 Advanced Consciousness Agent"
    echo "   • 💾 Memory Core Agent"
    echo "   • 🔄 Workflow Orchestration Agent"
    echo "   • 🔍 Information Retrieval Agent"
    echo "   • 📊 System Monitoring Agent"
    echo "   • 🛡️ Governance & Audit Agent"
    echo "   • ⚡ Data Pipeline Agent"
    echo ""
    print_status "📊 API Endpoints:"
    echo "   • Main Interface: $DOMAIN"
    echo "   • Health Check: $DOMAIN/health"
    echo "   • Agent List: $DOMAIN/agents"
    echo "   • Pipeline API: $DOMAIN/pipeline/process"
    echo ""
    print_warning "🚀 Your platform may take 1-2 minutes to fully initialize"
    
else
    print_error "❌ Deployment failed. Please check your Railway account and try again."
    exit 1
fi

print_success "✅ Deployment complete!"
