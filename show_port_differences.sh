#!/bin/bash

echo "🎯 DEMONSTRATING PORT DIFFERENCES FOR YOUR SOVEREIGN AGENT PLATFORM"
echo "=================================================================="
echo ""

echo "🔧 TESTING YOUR BACKEND (Sovereign Agent Platform):"
echo "Testing ports 8000, 8001, 8002 to find your running platform..."

for port in 8000 8001 8002; do
    echo ""
    echo "📡 Testing port $port:"
    response=$(curl -s --connect-timeout 3 http://localhost:$port/ 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$response" ]; then
        echo "✅ FOUND YOUR PLATFORM ON PORT $port!"
        echo "📄 Backend Response:"
        echo "$response" | head -3
        echo ""
        echo "🔗 Your Backend Endpoints:"
        echo "   • Platform Info: http://localhost:$port/"
        echo "   • All 7 Agents: http://localhost:$port/agents"
        echo "   • API Docs: http://localhost:$port/docs"
        echo "   • Health Check: http://localhost:$port/health"
        echo ""
        BACKEND_PORT=$port
        break
    else
        echo "❌ No response on port $port"
    fi
done

if [ -z "$BACKEND_PORT" ]; then
    echo "⚠️  Backend not responding - starting on port 8002..."
    cd "/home/behar/Desktop/New Folder"
    source .venv/bin/activate
    export PYTHONPATH=$PWD
    python -m uvicorn main:app --host 0.0.0.0 --port 8002 &
    BACKEND_PID=$!
    echo "🚀 Started backend on port 8002 (PID: $BACKEND_PID)"
    sleep 5
    BACKEND_PORT=8002
fi

echo ""
echo "🌐 NOW TESTING OPEN WEBUI (Frontend Chat Interface):"
echo "Checking if Open WebUI is available on port 8080..."

webui_response=$(curl -s --connect-timeout 3 http://localhost:8080/ 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$webui_response" ]; then
    echo "✅ Open WebUI is running on port 8080!"
    echo "🎨 Frontend Type: Web Chat Interface"
else
    echo "❌ Open WebUI not running on port 8080"
    echo "💡 To start Open WebUI:"
    echo "   docker run -d -p 8080:8080 -e WEBUI_AUTH=false ghcr.io/open-webui/open-webui:main"
fi

echo ""
echo "🎯 SUMMARY - THE KEY DIFFERENCES:"
echo "=================================="
echo ""
echo "🔧 PORT $BACKEND_PORT (Your Backend - Sovereign Agent Platform):"
echo "   • Content Type: JSON API responses"
echo "   • For: Developers, systems, API clients"
echo "   • Access: http://localhost:$BACKEND_PORT/docs"
echo "   • Purpose: Direct access to your 7 agents"
echo ""
echo "🌐 PORT 8080 (Frontend - Open WebUI):"
echo "   • Content Type: Beautiful web chat interface"
echo "   • For: End users, conversations"
echo "   • Access: http://localhost:8080"
echo "   • Purpose: ChatGPT-like experience with your agents"
echo ""
echo "💡 HOW TO SEE THE DIFFERENCES:"
echo "   1. Open http://localhost:$BACKEND_PORT/docs in browser → Technical API docs"
echo "   2. Open http://localhost:8080 in browser → Chat interface"
echo ""
echo "🎊 YOUR 7 AGENTS ARE AVAILABLE ON BOTH PORTS!"
