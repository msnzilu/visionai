#!/bin/bash

# Docker Swarm Initialization Script
# This script sets up Docker Swarm cluster on AWS EC2 instances

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Swarm Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if infrastructure summary exists
if [ ! -f "infrastructure-summary.txt" ]; then
  echo -e "${RED}Error: infrastructure-summary.txt not found${NC}"
  echo -e "${YELLOW}Please run setup-infrastructure.sh first${NC}"
  exit 1
fi

# Read configuration
source <(grep -E '^(Manager|Worker|SSH Key)' infrastructure-summary.txt | sed 's/: /=/g' | sed 's/ /_/g')

# Get manager IPs
echo -e "\n${YELLOW}Fetching instance IPs...${NC}"
MANAGER_IPS=($(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=visionai" "Name=tag:Role,Values=manager" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].PublicIpAddress' \
  --output text))

WORKER_IPS=($(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=visionai" "Name=tag:Role,Values=worker" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].PublicIpAddress' \
  --output text))

echo -e "${GREEN}Manager IPs: ${MANAGER_IPS[@]}${NC}"
echo -e "${GREEN}Worker IPs: ${WORKER_IPS[@]}${NC}"

# SSH options
SSH_OPTS="-i visionai-swarm-key.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

# Function to run command on remote host
run_remote() {
  local host=$1
  shift
  ssh $SSH_OPTS ubuntu@$host "$@"
}

# Install Docker on all nodes
echo -e "\n${YELLOW}Installing Docker on all nodes...${NC}"
for ip in "${MANAGER_IPS[@]}" "${WORKER_IPS[@]}"; do
  echo -e "${YELLOW}Installing Docker on $ip...${NC}"
  run_remote $ip 'bash -s' <<'ENDSSH'
    # Update system
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release

    # Add Docker GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Add ubuntu user to docker group
    sudo usermod -aG docker ubuntu

    # Enable Docker service
    sudo systemctl enable docker
    sudo systemctl start docker

    # Install NFS client for EFS
    sudo apt-get install -y nfs-common

    echo "Docker installed successfully"
ENDSSH
  echo -e "${GREEN}✓ Docker installed on $ip${NC}"
done

# Initialize Swarm on first manager
echo -e "\n${YELLOW}Initializing Docker Swarm on ${MANAGER_IPS[0]}...${NC}"
MANAGER_PRIVATE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=visionai" "Name=tag:Role,Values=manager" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].PrivateIpAddress' \
  --output text)

run_remote ${MANAGER_IPS[0]} "docker swarm init --advertise-addr $MANAGER_PRIVATE_IP"
echo -e "${GREEN}✓ Swarm initialized${NC}"

# Get join tokens
echo -e "\n${YELLOW}Getting join tokens...${NC}"
MANAGER_TOKEN=$(run_remote ${MANAGER_IPS[0]} "docker swarm join-token manager -q")
WORKER_TOKEN=$(run_remote ${MANAGER_IPS[0]} "docker swarm join-token worker -q")

# Join additional managers
echo -e "\n${YELLOW}Joining additional manager nodes...${NC}"
for i in "${!MANAGER_IPS[@]}"; do
  if [ $i -eq 0 ]; then continue; fi
  
  PRIVATE_IP=$(aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=visionai" "Name=tag:Role,Values=manager" "Name=instance-state-name,Values=running" \
    --query "Reservations[$i].Instances[0].PrivateIpAddress" \
    --output text)
  
  echo -e "${YELLOW}Joining manager ${MANAGER_IPS[$i]}...${NC}"
  run_remote ${MANAGER_IPS[$i]} "docker swarm join --token $MANAGER_TOKEN $MANAGER_PRIVATE_IP:2377"
  echo -e "${GREEN}✓ Manager ${MANAGER_IPS[$i]} joined${NC}"
done

# Join worker nodes
echo -e "\n${YELLOW}Joining worker nodes...${NC}"
for ip in "${WORKER_IPS[@]}"; do
  echo -e "${YELLOW}Joining worker $ip...${NC}"
  run_remote $ip "docker swarm join --token $WORKER_TOKEN $MANAGER_PRIVATE_IP:2377"
  echo -e "${GREEN}✓ Worker $ip joined${NC}"
done

# Label nodes for placement constraints
echo -e "\n${YELLOW}Labeling nodes...${NC}"

# Label automation workers (last 2 workers)
WORKER_COUNT=${#WORKER_IPS[@]}
if [ $WORKER_COUNT -ge 2 ]; then
  AUTOMATION_NODES=$(run_remote ${MANAGER_IPS[0]} "docker node ls --format '{{.Hostname}}' | tail -2")
  for node in $AUTOMATION_NODES; do
    run_remote ${MANAGER_IPS[0]} "docker node update --label-add workload=automation $node"
    echo -e "${GREEN}✓ Labeled $node for automation workload${NC}"
  done
fi

# Create overlay network
echo -e "\n${YELLOW}Creating overlay network...${NC}"
run_remote ${MANAGER_IPS[0]} "docker network create --driver overlay --attachable app-network"
echo -e "${GREEN}✓ Overlay network created${NC}"

# Mount EFS on all nodes
echo -e "\n${YELLOW}Mounting EFS on all nodes...${NC}"
EFS_ID=$(grep "EFS File System:" infrastructure-summary.txt | awk '{print $4}')
AWS_REGION=${AWS_REGION:-us-east-1}

for ip in "${MANAGER_IPS[@]}" "${WORKER_IPS[@]}"; do
  echo -e "${YELLOW}Mounting EFS on $ip...${NC}"
  run_remote $ip "bash -s" <<ENDSSH
    sudo mkdir -p /mnt/efs/uploads
    sudo mkdir -p /mnt/efs/logs
    
    # Add to fstab for persistent mount
    echo "$EFS_ID.efs.$AWS_REGION.amazonaws.com:/ /mnt/efs nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport 0 0" | sudo tee -a /etc/fstab
    
    # Mount
    sudo mount -a
    
    # Set permissions
    sudo chown -R ubuntu:ubuntu /mnt/efs
ENDSSH
  echo -e "${GREEN}✓ EFS mounted on $ip${NC}"
done

# Create Docker secrets (you'll need to provide these values)
echo -e "\n${YELLOW}Creating Docker secrets...${NC}"
echo -e "${YELLOW}You'll need to provide the following secrets:${NC}"

read -sp "OpenAI API Key: " OPENAI_KEY
echo
echo "$OPENAI_KEY" | run_remote ${MANAGER_IPS[0]} "docker secret create openai_api_key -"

read -sp "Stripe API Key: " STRIPE_KEY
echo
echo "$STRIPE_KEY" | run_remote ${MANAGER_IPS[0]} "docker secret create stripe_api_key -"

read -sp "JWT Secret: " JWT_SECRET
echo
echo "$JWT_SECRET" | run_remote ${MANAGER_IPS[0]} "docker secret create jwt_secret -"

read -p "Google OAuth Client ID: " GOOGLE_CLIENT_ID
echo "$GOOGLE_CLIENT_ID" | run_remote ${MANAGER_IPS[0]} "docker secret create google_oauth_client_id -"

read -sp "Google OAuth Client Secret: " GOOGLE_CLIENT_SECRET
echo
echo "$GOOGLE_CLIENT_SECRET" | run_remote ${MANAGER_IPS[0]} "docker secret create google_oauth_client_secret -"

echo -e "${GREEN}✓ Secrets created${NC}"

# Display cluster status
echo -e "\n${YELLOW}Cluster status:${NC}"
run_remote ${MANAGER_IPS[0]} "docker node ls"

# Save swarm info
cat > swarm-info.txt <<EOF
Docker Swarm Cluster Information
=================================

Manager Nodes:
$(for i in "${!MANAGER_IPS[@]}"; do echo "  Manager $((i+1)): ${MANAGER_IPS[$i]}"; done)

Worker Nodes:
$(for i in "${!WORKER_IPS[@]}"; do echo "  Worker $((i+1)): ${WORKER_IPS[$i]}"; done)

Primary Manager: ${MANAGER_IPS[0]}

Manager Join Token: $MANAGER_TOKEN
Worker Join Token: $WORKER_TOKEN

EFS Mount Point: /mnt/efs

Next Steps:
1. Configure GitHub Actions secrets
2. Push code to trigger deployment
3. Monitor deployment with: ssh -i visionai-swarm-key.pem ubuntu@${MANAGER_IPS[0]} "docker service ls"

SSH to primary manager:
ssh -i visionai-swarm-key.pem ubuntu@${MANAGER_IPS[0]}
EOF

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Swarm Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${GREEN}Swarm info saved to swarm-info.txt${NC}"
echo -e "${YELLOW}Primary manager: ${MANAGER_IPS[0]}${NC}"
