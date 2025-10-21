#!/bin/bash

# Define color variables
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Launching and preparing project...${NC}"

# Function to check and install missing tools
install_if_missing() {
  if ! command -v $1 &> /dev/null; then
    echo -e "${YELLOW}⚠️ $1 not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y $2
  else
    echo -e "${GREEN}✅ $1 is already installed.${NC}"
  fi
}

# Install core tools
install_if_missing docker docker.io
install_if_missing docker-compose docker-compose
install_if_missing ansible ansible
install_if_missing terraform terraform
install_if_missing python3 python3
install_if_missing pip3 python3-pip

# Ensure python3-venv is installed
if ! dpkg -l | grep -q python3-venv; then
  echo -e "${YELLOW}📦 Installing python3-venv...${NC}"
  sudo apt update
  sudo apt install -y python3-venv python3-full
fi

# Setup Python virtual environment using venv
if [ ! -d "venv" ]; then
  echo -e "${GREEN}🐍 Creating Python virtual environment using venv...${NC}"
  python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🌟 Activating Python virtual environment...${NC}"
source venv/bin/activate

# Install setuptools first (to fix distutils issue in Python 3.12)
echo "📦 Installing setuptools first..."
venv/bin/pip install --upgrade pip setuptools wheel

# Create a simplified requirements file for core functionality
echo -e "${YELLOW}📦 Creating a simplified requirements file for essential dependencies...${NC}"
echo -e "${CYAN}Writing requirements_core.txt file with essential dependencies${NC}"
cat > requirements_core.txt << EOL
# Core Framework
fastapi>=0.95.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
sqlalchemy>=2.0.0

# Database
aiosqlite>=0.17.0
psycopg2-binary>=2.9.0

# Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Utilities
python-dotenv>=1.0.0
websockets>=11.0.0
starlette>=0.27.0
httpx>=0.24.0
typing-extensions>=4.5.0
EOL
echo -e "${GREEN}✅ requirements_core.txt created successfully${NC}"

# 🔍 Install Python dependencies
echo -e "${YELLOW}📦 Installing core Python dependencies first...${NC}"
venv/bin/pip install -r requirements_core.txt

# Try installing the full requirements file if the core dependencies install successfully
if [ $? -eq 0 ]; then
  echo "📦 Core dependencies installed successfully. Attempting to install additional packages..."
  venv/bin/pip install -r requirements.txt || echo "⚠️ Some packages could not be installed. Core functionality should still work."
else
  echo "⚠️ Core dependencies installation failed. Please check the error messages above."
fi

# 🌱 Inject .env variables
if [ -f .env ]; then
  echo "🌿 Loading environment variables from .env..."
  export $(grep -v '^#' .env | xargs)
fi

# 🐳 Docker
if [ -f docker-compose.yml ]; then
  echo "🐳 Starting Docker containers..."
  docker compose up -d
fi

# 📦 Ansible
if [ -f setup.yml ]; then
  echo "📜 Running Ansible playbook..."
  ansible-playbook setup.yml
fi

# 🌍 Terraform
if [ -f main.tf ]; then
  echo "🌍 Applying Terraform config..."
  terraform init
  terraform apply -auto-approve
fi

echo -e "${GREEN}✅ All systems go. Project launched successfully.${NC}"
