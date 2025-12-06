#!/bin/bash

# Single Node Deployment Script
# Deploys Vision.AI to visionsai.store (13.51.158.58)

set -e

# Configuration
SERVER_IP="13.51.158.58"
SSH_USER="ubuntu"
SSH_KEY="visionai.pem" # Updated based on instance info
PROJECT_NAME="visionai"
AWS_REGION="eu-north-1" # As per user metadata

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying to $SERVER_IP${NC}"
echo -e "${GREEN}========================================${NC}"

# Check for SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${YELLOW}Warning: SSH Key '$SSH_KEY' not found in current directory.${NC}"
    echo -e "Please ensure you have the correct key file."
fi

# 1. Build and Push Images
# (Assuming ECR Registry URL is known or we get it via AWS CLI)
if [ -z "$ECR_REGISTRY" ]; then
    echo -e "${YELLOW}Fetching ECR Registry URL...${NC}"
    ECR_REGISTRY=$(aws ecr describe-repositories --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text 2>/dev/null | cut -d'/' -f1 || echo "")
    
    if [ -z "$ECR_REGISTRY" ]; then
        echo -e "${YELLOW}Could not auto-detect ECR Registry. Please set ECR_REGISTRY env var.${NC}"
        # Fallback for now if not set, might fail later
    fi
fi

if [ ! -z "$ECR_REGISTRY" ]; then
    echo -e "\n${YELLOW}Building and Pushing Images...${NC}"
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
    
    docker compose -f docker-compose.swarm.yml build
    
    # Tag and push
    for service in backend frontend automation; do
        docker tag visionai-$service:latest $ECR_REGISTRY/visionai:$service-latest
        docker push $ECR_REGISTRY/visionai:$service-latest
    done
else
    echo -e "${YELLOW}Skipping build/push (ECR_REGISTRY not found). Assuming images exist.${NC}"
fi

# 2. Deploy to Server
echo -e "\n${YELLOW}Deploying stack to server...${NC}"

# Copy stack file
scp -o StrictHostKeyChecking=no -i "$SSH_KEY" docker-compose.swarm.yml $SSH_USER@$SERVER_IP:~/

# Execute deployment
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" $SSH_USER@$SERVER_IP << EOF
    export ECR_REGISTRY=$ECR_REGISTRY
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
    
    # Pull latest images
    docker compose -f docker-compose.swarm.yml pull
    
    # Deploy stack
    docker stack deploy --compose-file docker-compose.swarm.yml visionai
    
    # Prune old images to save space on t3.micro
    docker image prune -f
EOF

echo -e "\n${GREEN}Deployment triggered.${NC}"
echo -e "Monitor status with: ssh -i $SSH_KEY $SSH_USER@$SERVER_IP 'docker service ls'"
