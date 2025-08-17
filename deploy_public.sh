#!/bin/bash

# Public Deployment Script for Sovereign Agent Platform with Open WebUI
# This script deploys your beautiful WebUI with all 7 agents for public access

set -e

echo "🚀 Deploying Sovereign Agent Platform with Open WebUI for Public Access"
echo "======================================================================"

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

echo ""
print_status "🎯 Deployment Options Available:"
echo ""
echo "1. 🌐 Local Network Access (Your Current Setup Enhanced)"
echo "   ✅ Open WebUI with all 7 agents"
echo "   📱 Accessible to devices on your local network"
echo "   🔗 Access via your local IP address"
echo ""
echo "2. ☁️  Cloud Deployment (Railway/Render/DigitalOcean)"
echo "   🌍 Public URL accessible from anywhere"
echo "   🔒 Built-in HTTPS and security"
echo "   📈 Auto-scaling and reliability"
echo ""
echo "3. 🐳 Docker + Nginx (Self-hosted with Domain)"
echo "   🏠 Deploy on your own server"
echo "   🌐 Custom domain name"
echo "   🛡️  Full control and security"
echo ""

read -p "Which deployment option would you like? (1/2/3): " choice

case $choice in
    1)
        print_status "🌐 Setting up Enhanced Local Network Access..."

        # Get local IP
        LOCAL_IP=$(hostname -I | cut -d' ' -f1)
        print_success "Your local IP: $LOCAL_IP"

        # Start enhanced services
        docker-compose -f docker-compose.public.yml up -d

        echo ""
        print_success "🎉 Enhanced Local Deployment Complete!"
        echo ""
        print_status "📱 Access your Sovereign Agent Platform:"
        echo "   • Local: http://localhost:8080"
        echo "   • Network: http://$LOCAL_IP:8080"
        echo "   • API: http://$LOCAL_IP:8000"
        echo ""
        print_status "🤖 All 7 Agents Available:"
        echo "   1. 🧠 Advanced Consciousness Agent"
        echo "   2. 💾 Memory Core Agent"
        echo "   3. 🔄 Workflow Orchestration Agent"
        echo "   4. 🔍 Information Retrieval Agent"
        echo "   5. 📊 System Monitoring Agent"
        echo "   6. 🛡️ Governance & Audit Agent"
        echo "   7. ⚡ Data Pipeline Agent"
        ;;

    2)
        print_status "☁️  Setting up Cloud Deployment..."

        echo ""
        print_status "🌟 Recommended Cloud Platforms:"
        echo ""
        echo "A. 🚂 Railway (Recommended - Easy deployment)"
        echo "   • Connect GitHub repository"
        echo "   • Automatic deployments"
        echo "   • Free tier available"
        echo ""
        echo "B. 🎨 Render"
        echo "   • Great for web applications"
        echo "   • Built-in SSL certificates"
        echo "   • Easy custom domains"
        echo ""
        echo "C. 🌊 DigitalOcean App Platform"
        echo "   • Professional deployment"
        echo "   • Scalable infrastructure"
        echo "   • Advanced features"
        echo ""

        read -p "Which cloud platform? (A/B/C): " platform

        case $platform in
            A|a)
                print_status "🚂 Setting up Railway deployment..."

                # Create railway.json
                cat > railway.json << EOF
{
  "version": 2,
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.webui"
  },
  "deploy": {
    "startCommand": "python -m uvicorn main:app --host 0.0.0.0 --port \$PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
EOF

                # Create railway-specific docker-compose
                cat > railway-compose.yml << EOF
version: '3.8'
services:
  sovereign-platform:
    build: .
    environment:
      - PORT=\$PORT
      - RAILWAY_STATIC_URL=\$RAILWAY_STATIC_URL
      - RAILWAY_GIT_COMMIT_SHA=\$RAILWAY_GIT_COMMIT_SHA
    volumes:
      - ./sovereign_webui_pipeline.py:/app/sovereign_webui_pipeline.py
EOF

                print_success "✅ Railway configuration created!"
                echo ""
                print_status "🚀 Next Steps for Railway Deployment:"
                echo "1. Go to https://railway.app"
                echo "2. Connect your GitHub repository"
                echo "3. Railway will auto-deploy your platform"
                echo "4. You'll get a public URL like: https://your-project.railway.app"
                ;;

            B|b)
                print_status "🎨 Setting up Render deployment..."

                # Create render.yaml
                cat > render.yaml << EOF
services:
  - type: web
    name: sovereign-agent-platform
    env: docker
    dockerfilePath: ./Dockerfile.webui
    envVars:
      - key: PORT
        value: 10000
      - key: PYTHONPATH
        value: /app
      - key: OPENWEBUI_INTEGRATION
        value: true
    healthCheckPath: /health
EOF

                print_success "✅ Render configuration created!"
                echo ""
                print_status "🚀 Next Steps for Render Deployment:"
                echo "1. Go to https://render.com"
                echo "2. Connect your GitHub repository"
                echo "3. Create new Web Service"
                echo "4. You'll get a public URL like: https://your-service.onrender.com"
                ;;

            C|c)
                print_status "🌊 Setting up DigitalOcean deployment..."

                # Create .do/app.yaml
                mkdir -p .do
                cat > .do/app.yaml << EOF
name: sovereign-agent-platform
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python -m uvicorn main:app --host 0.0.0.0 --port \$PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  health_check:
    http_path: /health
  envs:
  - key: PYTHONPATH
    value: /app
  - key: OPENWEBUI_INTEGRATION
    value: "true"
EOF

                print_success "✅ DigitalOcean configuration created!"
                echo ""
                print_status "🚀 Next Steps for DigitalOcean Deployment:"
                echo "1. Go to https://cloud.digitalocean.com/apps"
                echo "2. Create new App from GitHub"
                echo "3. Select your repository"
                echo "4. You'll get a public URL like: https://your-app.ondigitalocean.app"
                ;;
        esac
        ;;

    3)
        print_status "🐳 Setting up Docker + Nginx Self-hosted Deployment..."

        read -p "Enter your domain name (e.g., youragents.com): " domain

        # Update nginx.conf with actual domain
        sed -i "s/your-domain.com/$domain/g" nginx.conf

        # Deploy with Docker Compose
        docker-compose -f docker-compose.public.yml up -d

        print_success "✅ Self-hosted deployment started!"
        echo ""
        print_status "🌐 Your platform will be available at:"
        echo "   • http://$domain (after DNS setup)"
        echo "   • Local: http://localhost:8080"
        echo ""
        print_warning "📋 Additional steps needed:"
        echo "1. Point your domain's DNS to this server's IP"
        echo "2. Set up SSL certificates (Let's Encrypt recommended)"
        echo "3. Configure firewall to allow ports 80/443"
        ;;

    *)
        print_error "Invalid option. Please run the script again."
        exit 1
        ;;
esac

echo ""
print_success "🎊 Deployment Configuration Complete!"
echo ""
print_status "Your Sovereign Agent Platform with Open WebUI is ready!"
print_status "All 7 agents are now accessible through the beautiful web interface!"
echo ""
print_status "💡 Tips for using your deployed platform:"
echo "• Use function calling in chat: consciousness_query('analyze this')"
echo "• Upload documents for analysis by your retrieval agent"
echo "• Monitor system performance through the monitoring agent"
echo "• Create workflows using the orchestration agent"
echo ""
print_success "🚀 Your AI platform is now live and ready for public use!"
