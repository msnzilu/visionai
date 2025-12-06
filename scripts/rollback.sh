#!/bin/bash

# Rollback Script for Docker Swarm
# Rolls back all services to their previous version

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_NAME="visionai"

echo -e "${RED}========================================${NC}"
echo -e "${RED}Rolling Back Deployment${NC}"
echo -e "${RED}========================================${NC}"

# Get manager IP
MANAGER_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=${PROJECT_NAME}" "Name=tag:Role,Values=manager" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo -e "\n${YELLOW}Connecting to Swarm manager: $MANAGER_IP${NC}"

# Rollback all services
ssh -i ${PROJECT_NAME}-swarm-key.pem -o StrictHostKeyChecking=no ubuntu@$MANAGER_IP <<'EOF'
  echo "Rolling back all services..."
  
  for service in $(docker service ls --filter "label=com.docker.stack.namespace=visionai" --format "{{.Name}}"); do
    echo "Rolling back $service..."
    docker service rollback $service
  done
  
  echo "Waiting for rollback to complete..."
  sleep 30
  
  echo "Service status after rollback:"
  docker service ls
  
  echo "Rollback complete!"
EOF

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
