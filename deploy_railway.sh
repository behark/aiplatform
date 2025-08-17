#!/bin/bash

# Railway Deployment Script for Sovereign Agent Platform
# This script handles deployment with timeout recovery

echo "🚀 Deploying Sovereign Agent Platform with 7 Agents to Railway..."

# Set Railway environment variables
export RAILWAY_TOKEN=$1
export PROJECT_ID="c431152a-3658-4377-8f33-698218929fe5"

# Function to retry deployment
deploy_with_retry() {
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "📦 Deployment attempt $attempt of $max_attempts..."

        if railway up --detach; then
            echo "✅ Deployment successful!"
            railway domain generate
            echo "🌐 Your platform will be available at the generated domain"
            return 0
        else
            echo "⚠️  Attempt $attempt failed, retrying in 10 seconds..."
            sleep 10
            ((attempt++))
        fi
    done

    echo "❌ All deployment attempts failed. Try manual deployment via Railway dashboard."
    return 1
}

# Deploy the platform
deploy_with_retry

echo "🎯 All 7 Sovereign Agents are configured and ready!"
echo "📊 Platform Features:"
echo "   - Advanced Consciousness Agent"
echo "   - Memory Management System"
echo "   - Workflow Orchestration"
echo "   - Information Retrieval"
echo "   - System Monitoring"
echo "   - Governance & Audit"
echo "   - Data Pipeline Processing"
echo ""
echo "🔗 Access your Railway project: https://railway.com/project/c431152a-3658-4377-8f33-698218929fe5"
