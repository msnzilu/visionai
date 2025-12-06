#!/bin/bash

# Single Node Swarm Setup Script for Vision.AI
# Target: 13.51.158.58 (t3.micro)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Vision.AI SIngle Node Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Confirm execution
read -p "This script will setup Docker and Swap on the local machine. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Setup Swap (Critical for t3.micro)
echo -e "\n${YELLOW}Checking Swap space...${NC}"
if [ $(swapon --show | wc -l) -le 1 ]; then
    echo -e "${YELLOW}No swap detected. Creating 4GB swap file...${NC}"
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo -e "${GREEN}✓ 4GB Swap created${NC}"
else
    echo -e "${GREEN}✓ Swap already exists${NC}"
fi

# 2. Install Docker
echo -e "\n${YELLOW}Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
      
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    sudo usermod -aG docker ubuntu
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# 3. Initialize Swarm
echo -e "\n${YELLOW}Initializing Docker Swarm...${NC}"
if ! docker info | grep -q "Swarm: active"; then
    PRIVATE_IP=$(hostname -I | awk '{print $1}')
    sudo docker swarm init --advertise-addr $PRIVATE_IP
    echo -e "${GREEN}✓ Swarm initialized${NC}"
else
    echo -e "${GREEN}✓ Swarm already active${NC}"
fi

# 4. Create Network
echo -e "\n${YELLOW}Creating overlay network...${NC}"
if ! docker network ls | grep -q "app-network"; then
    sudo docker network create --driver overlay --attachable app-network
    echo -e "${GREEN}✓ Overlay network created${NC}"
fi

# 5. Setup Secrets
echo -e "\n${YELLOW}Setting up secrets...${NC}"
echo -e "${YELLOW}Please provide the following values (leave blank to skip if already set):${NC}"

setup_secret() {
    local secret_name=$1
    local prompt=$2
    if ! sudo docker secret ls | grep -q "$secret_name"; then
        read -sp "$prompt: " secret_value
        echo
        if [ ! -z "$secret_value" ]; then
            echo "$secret_value" | sudo docker secret create $secret_name -
            echo -e "${GREEN}✓ Secret $secret_name created${NC}"
        fi
    else
        echo -e "${GREEN}✓ Secret $secret_name already exists${NC}"
    fi
}

setup_secret "openai_api_key" "OpenAI API Key"
setup_secret "stripe_api_key" "Stripe API Key"
setup_secret "jwt_secret" "JWT Secret"
setup_secret "google_oauth_client_id" "Google Client ID"
setup_secret "google_oauth_client_secret" "Google Client Secret"

# 6. Auth with ECR (if aws cli configured)
if command -v aws &> /dev/null; then
    echo -e "\n${YELLOW}Logging into ECR...${NC}"
    AWS_REGION=${AWS_REGION:-eu-north-1}
    # Note: This assumes the instance has an IAM role or credentials configured
    aws ecr get-login-password --region $AWS_REGION | sudo docker login --username AWS --password-stdin $(aws ecr describe-repositories --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1) || echo -e "${YELLOW}ECR Login failed - check credentials${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "You can now deploy the stack using 'docker stack deploy ...'"
