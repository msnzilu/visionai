#!/bin/bash

# AWS Infrastructure Setup Script for Vision.AI
# This script provisions all necessary AWS resources for Docker Swarm deployment

set -e

# Configuration
PROJECT_NAME="visionai"
DOMAIN="visionsai.store"
AWS_REGION="${AWS_REGION:-us-east-1}"
VPC_CIDR="10.0.0.0/16"
KEY_NAME="${PROJECT_NAME}-swarm-key"

# Instance configuration
MANAGER_COUNT=3
WORKER_COUNT=3
MANAGER_INSTANCE_TYPE="t3.medium"
WORKER_INSTANCE_TYPE="t3.large"
AUTOMATION_INSTANCE_TYPE="t3.xlarge"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Vision.AI AWS Infrastructure Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required but not installed.${NC}" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}jq is required but not installed.${NC}" >&2; exit 1; }

# Verify AWS credentials
aws sts get-caller-identity >/dev/null 2>&1 || { echo -e "${RED}AWS credentials not configured.${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ AWS credentials verified${NC}"

# Create VPC
echo -e "\n${YELLOW}Creating VPC...${NC}"
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc},{Key=Project,Value=${PROJECT_NAME}}]" \
  --region $AWS_REGION \
  --query 'Vpc.VpcId' \
  --output text)
echo -e "${GREEN}✓ VPC created: $VPC_ID${NC}"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames \
  --region $AWS_REGION

# Create Internet Gateway
echo -e "\n${YELLOW}Creating Internet Gateway...${NC}"
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-igw},{Key=Project,Value=${PROJECT_NAME}}]" \
  --region $AWS_REGION \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)
echo -e "${GREEN}✓ Internet Gateway created: $IGW_ID${NC}"

# Attach IGW to VPC
aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID \
  --region $AWS_REGION

# Create Public Subnets (3 AZs)
echo -e "\n${YELLOW}Creating subnets across 3 availability zones...${NC}"
AVAILABILITY_ZONES=($(aws ec2 describe-availability-zones --region $AWS_REGION --query 'AvailabilityZones[0:3].ZoneName' --output text))
PUBLIC_SUBNET_IDS=()

for i in {0..2}; do
  SUBNET_CIDR="10.0.$((i+1)).0/24"
  SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block $SUBNET_CIDR \
    --availability-zone ${AVAILABILITY_ZONES[$i]} \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-subnet-$((i+1))},{Key=Project,Value=${PROJECT_NAME}}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text)
  
  PUBLIC_SUBNET_IDS+=($SUBNET_ID)
  
  # Enable auto-assign public IP
  aws ec2 modify-subnet-attribute \
    --subnet-id $SUBNET_ID \
    --map-public-ip-on-launch \
    --region $AWS_REGION
  
  echo -e "${GREEN}✓ Public subnet created: $SUBNET_ID (${AVAILABILITY_ZONES[$i]})${NC}"
done

# Create Route Table
echo -e "\n${YELLOW}Creating route table...${NC}"
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-rt},{Key=Project,Value=${PROJECT_NAME}}]" \
  --region $AWS_REGION \
  --query 'RouteTable.RouteTableId' \
  --output text)
echo -e "${GREEN}✓ Route table created: $ROUTE_TABLE_ID${NC}"

# Create route to Internet Gateway
aws ec2 create-route \
  --route-table-id $ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region $AWS_REGION

# Associate route table with subnets
for SUBNET_ID in "${PUBLIC_SUBNET_IDS[@]}"; do
  aws ec2 associate-route-table \
    --subnet-id $SUBNET_ID \
    --route-table-id $ROUTE_TABLE_ID \
    --region $AWS_REGION
done

# Create Security Groups
echo -e "\n${YELLOW}Creating security groups...${NC}"

# Manager Security Group
MANAGER_SG_ID=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-manager-sg" \
  --description "Security group for Docker Swarm manager nodes" \
  --vpc-id $VPC_ID \
  --region $AWS_REGION \
  --query 'GroupId' \
  --output text)
echo -e "${GREEN}✓ Manager security group created: $MANAGER_SG_ID${NC}"

# Worker Security Group
WORKER_SG_ID=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-worker-sg" \
  --description "Security group for Docker Swarm worker nodes" \
  --vpc-id $VPC_ID \
  --region $AWS_REGION \
  --query 'GroupId' \
  --output text)
echo -e "${GREEN}✓ Worker security group created: $WORKER_SG_ID${NC}"

# ALB Security Group
ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name "${PROJECT_NAME}-alb-sg" \
  --description "Security group for Application Load Balancer" \
  --vpc-id $VPC_ID \
  --region $AWS_REGION \
  --query 'GroupId' \
  --output text)
echo -e "${GREEN}✓ ALB security group created: $ALB_SG_ID${NC}"

# Configure Security Group Rules
echo -e "\n${YELLOW}Configuring security group rules...${NC}"

# ALB rules (HTTP/HTTPS from internet)
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $AWS_REGION

# Manager rules
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $AWS_REGION  # SSH
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol tcp --port 2377 --source-group $MANAGER_SG_ID --region $AWS_REGION  # Swarm management
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol tcp --port 2377 --source-group $WORKER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol tcp --port 7946 --source-group $MANAGER_SG_ID --region $AWS_REGION  # Container network discovery
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol udp --port 7946 --source-group $MANAGER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol udp --port 4789 --source-group $MANAGER_SG_ID --region $AWS_REGION  # Overlay network
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol tcp --port 80 --source-group $ALB_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $MANAGER_SG_ID --protocol tcp --port 443 --source-group $ALB_SG_ID --region $AWS_REGION

# Worker rules
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol tcp --port 7946 --source-group $MANAGER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol udp --port 7946 --source-group $MANAGER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol udp --port 4789 --source-group $MANAGER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol tcp --port 7946 --source-group $WORKER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol udp --port 7946 --source-group $WORKER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol udp --port 4789 --source-group $WORKER_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol tcp --port 80 --source-group $ALB_SG_ID --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $WORKER_SG_ID --protocol tcp --port 443 --source-group $ALB_SG_ID --region $AWS_REGION

echo -e "${GREEN}✓ Security group rules configured${NC}"

# Create Key Pair
echo -e "\n${YELLOW}Creating EC2 key pair...${NC}"
aws ec2 create-key-pair \
  --key-name $KEY_NAME \
  --region $AWS_REGION \
  --query 'KeyMaterial' \
  --output text > ${KEY_NAME}.pem
chmod 400 ${KEY_NAME}.pem
echo -e "${GREEN}✓ Key pair created and saved to ${KEY_NAME}.pem${NC}"

# Get latest Ubuntu AMI
echo -e "\n${YELLOW}Finding latest Ubuntu 22.04 AMI...${NC}"
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --region $AWS_REGION \
  --output text)
echo -e "${GREEN}✓ Using AMI: $AMI_ID${NC}"

# Launch Manager Instances
echo -e "\n${YELLOW}Launching $MANAGER_COUNT manager instances...${NC}"
MANAGER_INSTANCE_IDS=()

for i in $(seq 1 $MANAGER_COUNT); do
  SUBNET_INDEX=$((($i - 1) % 3))
  INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $MANAGER_INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $MANAGER_SG_ID \
    --subnet-id ${PUBLIC_SUBNET_IDS[$SUBNET_INDEX]} \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-manager-$i},{Key=Project,Value=${PROJECT_NAME}},{Key=Role,Value=manager}]" \
    --region $AWS_REGION \
    --query 'Instances[0].InstanceId' \
    --output text)
  
  MANAGER_INSTANCE_IDS+=($INSTANCE_ID)
  echo -e "${GREEN}✓ Manager $i launched: $INSTANCE_ID${NC}"
done

# Launch Worker Instances
echo -e "\n${YELLOW}Launching $WORKER_COUNT worker instances...${NC}"
WORKER_INSTANCE_IDS=()

for i in $(seq 1 $WORKER_COUNT); do
  SUBNET_INDEX=$((($i - 1) % 3))
  INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $WORKER_INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $WORKER_SG_ID \
    --subnet-id ${PUBLIC_SUBNET_IDS[$SUBNET_INDEX]} \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-worker-$i},{Key=Project,Value=${PROJECT_NAME}},{Key=Role,Value=worker}]" \
    --region $AWS_REGION \
    --query 'Instances[0].InstanceId' \
    --output text)
  
  WORKER_INSTANCE_IDS+=($INSTANCE_ID)
  echo -e "${GREEN}✓ Worker $i launched: $INSTANCE_ID${NC}"
done

# Wait for instances to be running
echo -e "\n${YELLOW}Waiting for instances to be running...${NC}"
ALL_INSTANCE_IDS=("${MANAGER_INSTANCE_IDS[@]}" "${WORKER_INSTANCE_IDS[@]}")
aws ec2 wait instance-running --instance-ids ${ALL_INSTANCE_IDS[@]} --region $AWS_REGION
echo -e "${GREEN}✓ All instances are running${NC}"

# Create Application Load Balancer
echo -e "\n${YELLOW}Creating Application Load Balancer...${NC}"
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ${PROJECT_NAME}-alb \
  --subnets ${PUBLIC_SUBNET_IDS[@]} \
  --security-groups $ALB_SG_ID \
  --region $AWS_REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)
echo -e "${GREEN}✓ ALB created: $ALB_ARN${NC}"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --region $AWS_REGION \
  --query 'LoadBalancers[0].DNSName' \
  --output text)
echo -e "${GREEN}✓ ALB DNS: $ALB_DNS${NC}"

# Create Target Groups
echo -e "\n${YELLOW}Creating target groups...${NC}"

# HTTP Target Group
HTTP_TG_ARN=$(aws elbv2 create-target-group \
  --name ${PROJECT_NAME}-http-tg \
  --protocol HTTP \
  --port 80 \
  --vpc-id $VPC_ID \
  --health-check-path /api/v1/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region $AWS_REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)
echo -e "${GREEN}✓ HTTP target group created${NC}"

# Register instances with target group
aws elbv2 register-targets \
  --target-group-arn $HTTP_TG_ARN \
  --targets $(printf "Id=%s " "${ALL_INSTANCE_IDS[@]}") \
  --region $AWS_REGION

# Create ALB Listener (HTTP)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$HTTP_TG_ARN \
  --region $AWS_REGION

echo -e "${GREEN}✓ ALB listener created${NC}"

# Request SSL Certificate
echo -e "\n${YELLOW}Requesting SSL certificate for $DOMAIN...${NC}"
CERT_ARN=$(aws acm request-certificate \
  --domain-name $DOMAIN \
  --subject-alternative-names "*.$DOMAIN" \
  --validation-method DNS \
  --region $AWS_REGION \
  --query 'CertificateArn' \
  --output text)
echo -e "${GREEN}✓ Certificate requested: $CERT_ARN${NC}"
echo -e "${YELLOW}⚠ You need to validate this certificate via DNS before it can be used${NC}"

# Create ECR Repositories
echo -e "\n${YELLOW}Creating ECR repositories...${NC}"
for service in backend frontend automation; do
  aws ecr create-repository \
    --repository-name ${PROJECT_NAME}-${service} \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    2>/dev/null || echo "Repository ${PROJECT_NAME}-${service} already exists"
  echo -e "${GREEN}✓ ECR repository: ${PROJECT_NAME}-${service}${NC}"
done

# Create EFS for shared storage
echo -e "\n${YELLOW}Creating EFS file system for shared storage...${NC}"
EFS_ID=$(aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --tags Key=Name,Value=${PROJECT_NAME}-efs Key=Project,Value=${PROJECT_NAME} \
  --region $AWS_REGION \
  --query 'FileSystemId' \
  --output text)
echo -e "${GREEN}✓ EFS created: $EFS_ID${NC}"

# Create EFS mount targets
for i in {0..2}; do
  aws efs create-mount-target \
    --file-system-id $EFS_ID \
    --subnet-id ${PUBLIC_SUBNET_IDS[$i]} \
    --security-groups $MANAGER_SG_ID \
    --region $AWS_REGION
done
echo -e "${GREEN}✓ EFS mount targets created${NC}"

# Output summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Infrastructure Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

cat > infrastructure-summary.txt <<EOF
Vision.AI AWS Infrastructure Summary
=====================================

VPC ID: $VPC_ID
Internet Gateway: $IGW_ID
Public Subnets: ${PUBLIC_SUBNET_IDS[@]}

Security Groups:
- Manager SG: $MANAGER_SG_ID
- Worker SG: $WORKER_SG_ID
- ALB SG: $ALB_SG_ID

EC2 Instances:
Manager Nodes: ${MANAGER_INSTANCE_IDS[@]}
Worker Nodes: ${WORKER_INSTANCE_IDS[@]}

Load Balancer:
- ARN: $ALB_ARN
- DNS: $ALB_DNS

SSL Certificate ARN: $CERT_ARN

EFS File System: $EFS_ID

ECR Registry: $(aws ecr describe-repositories --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)

SSH Key: ${KEY_NAME}.pem

Next Steps:
1. Validate SSL certificate via DNS
2. Point $DOMAIN to $ALB_DNS
3. Run setup-swarm.sh to initialize Docker Swarm
4. Configure GitHub Actions secrets
5. Deploy application

Manager 1 IP (for SSH): $(aws ec2 describe-instances --instance-ids ${MANAGER_INSTANCE_IDS[0]} --region $AWS_REGION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
EOF

echo -e "\n${GREEN}Summary saved to infrastructure-summary.txt${NC}"
echo -e "${YELLOW}Please review the next steps in the summary file${NC}"
