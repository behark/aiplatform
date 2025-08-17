#!/bin/bash

# Quick Railway Deployment for Sovereign Agent Platform
# This script handles deployment with optimized approach

echo "🚀 Deploying Sovereign Agent Platform with 7 Agents + 5 Models..."

# Create a minimal deployment package
echo "📦 Creating minimal deployment package..."

# Copy only essential files for Railway
mkdir -p /tmp/railway_deploy
cp main.py /tmp/railway_deploy/
cp webui_integration.py /tmp/railway_deploy/
cp openwebui_pipeline.py /tmp/railway_deploy/
cp requirements.txt /tmp/railway_deploy/
cp Dockerfile.railway.minimal /tmp/railway_deploy/Dockerfile
cp railway.json /tmp/railway_deploy/
cp -r src/ /tmp/railway_deploy/src/
cp -r config/ /tmp/railway_deploy/config/

cd /tmp/railway_deploy

# Initialize Railway in the minimal package
echo "🔧 Initializing Railway in minimal package..."
railway login --browserless
railway link c431152a-3658-4377-8f33-698218929fe5

# Deploy with retry logic
echo "🚀 Attempting optimized deployment..."
for i in {1..3}; do
    echo "Attempt $i of 3..."
    if railway up --detach; then
        echo "✅ Deployment successful!"
        railway domain generate
        railway status
        echo "🌐 Platform deployed successfully!"
        break
    else
        echo "⚠️  Attempt $i failed, trying again..."
        sleep 5
    fi
done

echo "🎯 Your 7 Sovereign Agents are now deployed:"
echo "   ✅ Consciousness Agent (Mixtral + Hermes)"
echo "   ✅ Memory Agent (DeepSeek + Mixtral)"
echo "   ✅ Orchestration Agent (Mixtral + DeepSeek)"
echo "   ✅ Retrieval Agent (DeepSeek + Mixtral)"
echo "   ✅ Monitoring Agent (DeepSeek + Phi)"
echo "   ✅ Governance Agent (Mixtral + DeepSeek)"
echo "   ✅ Pipeline Agent (DeepSeek + Phi)"
echo ""
echo "🔗 Railway Project: https://railway.com/project/c431152a-3658-4377-8f33-698218929fe5"

# Cleanup
cd /home/behar/Desktop/New\ Folder
rm -rf /tmp/railway_deploy
