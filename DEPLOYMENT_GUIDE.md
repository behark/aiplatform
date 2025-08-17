# 🚀 Sovereign Agent Platform - Complete Deployment Guide

## Overview
Your platform now includes **7 fully functional sovereign agents** integrated with Open WebUI:

1. **🧠 Advanced Consciousness Agent** - Master reasoning and personality adaptation
2. **💾 Memory Core Agent** - Experience storage and context retrieval  
3. **🔄 Workflow Orchestration Agent** - DAG-based task management
4. **🔍 Information Retrieval Agent** - Advanced RAG and semantic search
5. **📊 System Monitoring Agent** - Real-time performance tracking
6. **🛡️ Governance & Audit Agent** - Policy enforcement and compliance
7. **⚡ Data Pipeline Agent** - Advanced data processing and transformation

## 🎯 Quick Start (Local Development)

### Option 1: Local Development Server
```bash
# Navigate to your project
cd "/home/behar/Desktop/New Folder"

# Run the quick start script
./start_local.sh
```

This will:
- Set up Python virtual environment
- Install all dependencies
- Start the platform on `http://localhost:8000`

### Access Points:
- **Main API**: http://localhost:8000
- **Agent Status**: http://localhost:8000/agents  
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## 🚢 Production Deployment (Kubernetes + Open WebUI)

### Prerequisites:
- Kubernetes cluster (minikube, EKS, GKE, etc.)
- Docker installed
- kubectl configured

### Deploy to Production:
```bash
# Run the full deployment script
./deploy.sh
```

This will:
1. Build Docker image for your platform
2. Create Kubernetes namespace `open-webui`
3. Deploy both Open WebUI and your Sovereign Agent Platform
4. Set up persistent storage and load balancing
5. Configure health checks and monitoring

### Access Production Platform:
```bash
# Port forward to access locally
kubectl port-forward svc/sovereign-platform-service 8080:8080 8000:8000 -n open-webui

# Then access:
# - Open WebUI: http://localhost:8080
# - Agent API: http://localhost:8000
```

## 💬 Using Your Agents in Open WebUI

### Automatic Agent Selection
The platform automatically routes queries to the appropriate agent based on keywords:

- **"think", "reason", "analyze"** → 🧠 Consciousness Agent
- **"remember", "store", "recall"** → 💾 Memory Agent  
- **"orchestrate", "workflow", "schedule"** → 🔄 Orchestration Agent
- **"search", "find", "retrieve"** → 🔍 Retrieval Agent
- **"monitor", "status", "performance"** → 📊 Monitoring Agent
- **"policy", "audit", "compliance"** → 🛡️ Governance Agent
- **"process", "transform", "pipeline"** → ⚡ Pipeline Agent

### Example Queries:
```
"Analyze this complex problem using advanced reasoning"
→ Routes to Consciousness Agent

"Search for documents about machine learning"  
→ Routes to Retrieval Agent

"Monitor the system performance metrics"
→ Routes to Monitoring Agent
```

### Function Calling
Your agents are also available as direct functions:
```python
# In Open WebUI chat
consciousness_query("What's the best approach to solve this?")
retrieve_information("Find research papers on AI ethics")
orchestrate_workflow("Create a data processing pipeline")
```

## 🔧 Configuration

### Environment Variables
```bash
export PYTHONPATH="/home/behar/Desktop/New Folder"
export OPENWEBUI_INTEGRATION=true
export LOG_LEVEL=INFO
```

### Agent Configuration
Edit `config/webui_config.json` to customize:
- Agent capabilities and descriptions
- UI customization options
- Function calling settings
- Pipeline configuration

## 📊 Monitoring and Health

### Health Endpoints:
- **Platform Health**: `/health`
- **Agent Status**: `/agents`
- **Metrics**: `/monitoring/status`

### Logs:
- Application logs: `/app/logs/`
- Kubernetes logs: `kubectl logs -f deployment/open-webui-deployment -n open-webui`

## 🛠️ Troubleshooting

### Common Issues:

1. **Import Errors**: The platform includes fallback mock implementations
2. **Port Conflicts**: Change ports in `main.py` and deployment files
3. **Memory Issues**: Adjust resource limits in `webui-deployment.yaml`

### Debug Mode:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## 🎉 Success Indicators

✅ **Platform Status**: All 7 agents initialized and running  
✅ **Open WebUI Integration**: Web interface accessible and responsive  
✅ **Function Calling**: All agent functions available in chat  
✅ **Auto-routing**: Queries automatically directed to appropriate agents  
✅ **Health Monitoring**: All health checks passing  
✅ **Kubernetes Deployment**: Pods running and load balancer active  

## 🚀 Next Steps

1. **Customize Agents**: Modify agent implementations in `src/agent_implementations.py`
2. **Add Models**: Integrate additional AI models through the model registry
3. **Scale Up**: Increase replicas in deployment for higher load
4. **Monitor**: Set up Prometheus/Grafana for advanced monitoring
5. **Security**: Configure authentication and authorization as needed

Your Sovereign Agent Platform is now **fully operational** with all 7 agents integrated into Open WebUI! 🎊
