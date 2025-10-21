#!/bin/bash

# Complete Railway Deployment Script for Sovereign Agent Platform
# This script deploys both backend API and WebUI components

echo "🚀 Deploying Complete Sovereign Agent Platform to Railway..."
echo "   - Backend API on port 8000"
echo "   - WebUI Interface on port 8080"

# Set Railway environment variables if provided
if [ ! -z "$1" ]; then
  export RAILWAY_TOKEN=$1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    curl -fsSL https://railway.app/install.sh | sh
fi

# Login check
railway login --browserless

echo "📦 Starting deployment using multi-service configuration..."
railway up --detach --service=sovereign-platform --service=open-webui

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"

    # Generate domain
    echo "🌐 Generating domain for your deployment..."
    railway domain generate

    echo ""
    echo "🎉 COMPLETE DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "🎯 Your platform should now be accessible at the generated Railway domain"
    echo "   The WebUI will be available at the domain root (port 8080)"
    echo "   The Backend API will be available at the same domain on path /api (port 8000)"
    echo ""
    echo "💡 Note: It may take a few minutes for both services to fully start up"
else
    echo "❌ Deployment failed. Please check Railway logs for details."
fi
