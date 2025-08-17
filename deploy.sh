#!/bin/bash

# Deployment script for Sovereign Agent Platform with Open WebUI
# This script builds and deploys the complete platform with all 7 agents

set -e

echo "🚀 Starting Sovereign Agent Platform Deployment..."

# Configuration
NAMESPACE="open-webui"
PLATFORM_IMAGE="sovereign-platform:latest"
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Create namespace if it doesn't exist
print_status "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Step 2: Build Docker image
print_status "Building Docker image for Sovereign Agent Platform..."
docker build -f Dockerfile.webui -t ${PLATFORM_IMAGE} .

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Step 3: Tag and push to registry if specified
if [ "${DOCKER_REGISTRY}" != "localhost:5000" ]; then
    print_status "Tagging and pushing image to ${DOCKER_REGISTRY}..."
    docker tag ${PLATFORM_IMAGE} ${DOCKER_REGISTRY}/${PLATFORM_IMAGE}
    docker push ${DOCKER_REGISTRY}/${PLATFORM_IMAGE}
fi

# Step 4: Apply Kubernetes manifests
print_status "Applying Kubernetes manifests..."

# Apply PVCs first
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: open-webui-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sovereign-platform-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sovereign-logs-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

print_success "PVCs created"

# Step 5: Apply main deployment
print_status "Deploying the platform..."
kubectl apply -f deployment/webui-deployment.yaml

# Step 6: Wait for deployment to be ready
print_status "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/open-webui-deployment -n ${NAMESPACE}

# Step 7: Get service information
print_status "Getting service information..."
kubectl get services -n ${NAMESPACE}

# Step 8: Port forward for local access (optional)
print_warning "To access the platform locally, run:"
echo "kubectl port-forward svc/sovereign-platform-service 8080:8080 8000:8000 -n ${NAMESPACE}"

print_success "🎉 Sovereign Agent Platform deployed successfully!"

# Step 9: Display agent information
print_status "Your 7 Sovereign Agents are now available:"
echo "1. 🧠 Advanced Consciousness Agent - Master reasoning and personality adaptation"
echo "2. 💾 Memory Core Agent - Experience storage and context retrieval"
echo "3. 🔄 Workflow Orchestration Agent - DAG-based task management"
echo "4. 🔍 Information Retrieval Agent - Advanced RAG and semantic search"
echo "5. 📊 System Monitoring Agent - Real-time performance tracking"
echo "6. 🛡️ Governance & Audit Agent - Policy enforcement and compliance"
echo "7. ⚡ Data Pipeline Agent - Advanced data processing and transformation"

echo ""
print_status "Platform URLs:"
echo "• Open WebUI: http://localhost:8080 (after port-forward)"
echo "• Agent API: http://localhost:8000 (after port-forward)"
echo "• Health Check: http://localhost:8000/health"
echo "• Agent Status: http://localhost:8000/agents"

echo ""
print_success "Deployment completed successfully! 🚀"
