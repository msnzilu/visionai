#!/bin/bash

# Manual Deployment Script for Docker Swarm
# Use this for manual deployments or when GitHub Actions is not available

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_NAME="visionai"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REGISTRY="${ECR_REGISTRY}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Vision.AI Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required${NC}" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required${NC}" >&2; exit 1; }

# Get ECR registry if not set
if [ -z "$ECR_REGISTRY" ]; then
  ECR_REGISTRY=$(aws ecr describe-repositories --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)
  echo -e "${GREEN}Using ECR registry: $ECR_REGISTRY${NC}"
fi

# Login to ECR
echo -e "\n${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Build and push images
echo -e "\n${YELLOW}Building Docker images...${NC}"

# Backend
echo -e "${YELLOW}Building backend...${NC}"
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}-backend:${IMAGE_TAG} ./backend
docker push ${ECR_REGISTRY}/${PROJECT_NAME}-backend:${IMAGE_TAG}
echo -e "${GREEN}✓ Backend image pushed${NC}"

# Frontend
echo -e "${YELLOW}Building frontend...${NC}"
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}-frontend:${IMAGE_TAG} ./frontend
docker push ${ECR_REGISTRY}/${PROJECT_NAME}-frontend:${IMAGE_TAG}
echo -e "${GREEN}✓ Frontend image pushed${NC}"

# Browser Automation
echo -e "${YELLOW}Building browser automation...${NC}"
docker build -t ${ECR_REGISTRY}/${PROJECT_NAME}-automation:${IMAGE_TAG} ./browser-automation
docker push ${ECR_REGISTRY}/${PROJECT_NAME}-automation:${IMAGE_TAG}
echo -e "${GREEN}✓ Automation image pushed${NC}"

# Get manager IP
MANAGER_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=${PROJECT_NAME}" "Name=tag:Role,Values=manager" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo -e "\n${YELLOW}Deploying to Swarm manager: $MANAGER_IP${NC}"

# Copy docker-compose file to manager
scp -i ${PROJECT_NAME}-swarm-key.pem -o StrictHostKeyChecking=no \
  docker-compose.swarm.yml \
  ubuntu@$MANAGER_IP:/tmp/

# Deploy stack
ssh -i ${PROJECT_NAME}-swarm-key.pem -o StrictHostKeyChecking=no ubuntu@$MANAGER_IP <<EOF
  # Set environment variables
  export ECR_REGISTRY=$ECR_REGISTRY
  export IMAGE_TAG=$IMAGE_TAG
  export MONGO_USER=${MONGO_USER}
  export MONGO_PASSWORD=${MONGO_PASSWORD}
  export MONGO_HOST=${MONGO_HOST}
  export MONGO_DB=${MONGO_DB:-job_platform}
  export REDIS_HOST=${REDIS_HOST}
  export NFS_SERVER=${NFS_SERVER:-localhost}
  
  # Login to ECR
  aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
  
  # Deploy stack
  echo "Deploying stack..."
  docker stack deploy \
    --compose-file /tmp/docker-compose.swarm.yml \
    --with-registry-auth \
    ${PROJECT_NAME}
  
  # Wait for deployment
  echo "Waiting for services to start..."
  sleep 30
  
  # Check service status
  echo "Service status:"
  docker service ls
  
  # Check for any failed services
  FAILED=\$(docker service ls --filter "label=com.docker.stack.namespace=${PROJECT_NAME}" --format "{{.Replicas}}" | grep "0/")
  if [ ! -z "\$FAILED" ]; then
    echo "Warning: Some services may have failed to start"
    docker service ls
  else
    echo "All services started successfully!"
  fi
EOF

# Verify deployment
echo -e "\n${YELLOW}Verifying deployment...${NC}"
sleep 10

# Check health endpoint
if curl -f -s https://webtestingdomain.online/api/v1/health > /dev/null; then
  echo -e "${GREEN}✓ Health check passed${NC}"
else
  echo -e "${YELLOW}⚠ Health check failed - services may still be starting${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${GREEN}Application URL: https://webtestingdomain.online${NC}"
echo -e "${YELLOW}Monitor services: ssh -i ${PROJECT_NAME}-swarm-key.pem ubuntu@$MANAGER_IP 'docker service ls'${NC}"
