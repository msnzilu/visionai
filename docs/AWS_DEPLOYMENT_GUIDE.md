# AWS Deployment Guide - Vision.AI

Complete step-by-step guide to deploy Vision.AI to AWS using Docker Swarm with zero-downtime CI/CD.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Docker installed locally
- Git repository access
- Domain: **webtestingdomain.online**

## Step 1: Prepare External Services

### MongoDB Atlas Setup

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster (M10 or higher recommended for production)
3. Create a database user with read/write permissions
4. Whitelist AWS IP ranges or use VPC peering
5. Get connection string: `mongodb+srv://user:password@cluster.mongodb.net/job_platform`

### Redis ElastiCache Setup

1. Go to AWS ElastiCache console
2. Create Redis cluster:
   - Engine: Redis 7.x
   - Node type: cache.t3.medium (minimum)
   - Number of replicas: 2
   - Multi-AZ: Enabled
3. Note the primary endpoint

## Step 2: Run Infrastructure Setup

```bash
cd aws
chmod +x setup-infrastructure.sh
./setup-infrastructure.sh
```

This script will create:
- VPC with 3 public subnets across availability zones
- Security groups for managers, workers, and ALB
- EC2 instances (3 managers + 3 workers)
- Application Load Balancer
- SSL certificate request
- ECR repositories
- EFS file system

**Important**: Save the `infrastructure-summary.txt` file generated.

## Step 3: Validate SSL Certificate

1. Go to AWS Certificate Manager console
2. Find the certificate for `webtestingdomain.online`
3. Add the CNAME records to your DNS provider
4. Wait for validation (usually 5-30 minutes)

## Step 4: Configure DNS

Point your domain to the ALB:

1. Get ALB DNS from `infrastructure-summary.txt`
2. In your DNS provider, create:
   - A record (or ALIAS if Route 53): `webtestingdomain.online` → ALB DNS
   - CNAME: `*.webtestingdomain.online` → ALB DNS

## Step 5: Initialize Docker Swarm

```bash
cd aws
chmod +x setup-swarm.sh
./setup-swarm.sh
```

This will:
- Install Docker on all nodes
- Initialize Swarm cluster
- Join manager and worker nodes
- Create overlay networks
- Mount EFS storage
- Create Docker secrets

You'll be prompted to enter:
- OpenAI API key
- Stripe API key
- JWT secret
- Google OAuth credentials

## Step 6: Configure GitHub Actions Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

```
AWS_ACCESS_KEY_ID=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
ECR_REGISTRY=<account_id>.dkr.ecr.us-east-1.amazonaws.com
SWARM_MANAGER_HOST=<manager_1_public_ip>
SWARM_SSH_PRIVATE_KEY=<contents_of_visionai-swarm-key.pem>
MONGO_USER=<mongodb_username>
MONGO_PASSWORD=<mongodb_password>
MONGO_HOST=<mongodb_atlas_host>
MONGO_DB=job_platform
REDIS_HOST=<elasticache_endpoint>
NFS_SERVER=<efs_id>.efs.us-east-1.amazonaws.com
```

## Step 7: Deploy Application

### Option A: Automated Deployment (Recommended)

Push to main branch:
```bash
git add .
git commit -m "Deploy to AWS"
git push origin main
```

GitHub Actions will automatically:
1. Run tests
2. Build Docker images
3. Push to ECR
4. Deploy to Swarm with rolling updates

### Option B: Manual Deployment

```bash
# Set environment variables
export ECR_REGISTRY=<your_ecr_registry>
export MONGO_USER=<user>
export MONGO_PASSWORD=<password>
export MONGO_HOST=<host>
export REDIS_HOST=<redis_endpoint>

# Run deployment script
chmod +x scripts/deploy-swarm.sh
./scripts/deploy-swarm.sh
```

## Step 8: Verify Deployment

1. **Check service status**:
   ```bash
   ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> "docker service ls"
   ```

2. **Check service logs**:
   ```bash
   ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> "docker service logs visionai_backend"
   ```

3. **Test health endpoint**:
   ```bash
   curl https://webtestingdomain.online/api/v1/health
   ```

4. **Access application**:
   - Open https://webtestingdomain.online in browser
   - Test user registration and login
   - Upload a CV and test analysis
   - Test job search functionality

## Step 9: Configure SSL on ALB (Optional)

If you want SSL termination at ALB instead of Traefik:

1. Go to EC2 → Load Balancers
2. Select your ALB
3. Add HTTPS listener (port 443)
4. Select the validated ACM certificate
5. Forward to HTTP target group

## Monitoring and Maintenance

### View Service Status
```bash
ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> "docker service ls"
```

### Scale Services
```bash
ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> "docker service scale visionai_backend=5"
```

### View Logs
```bash
ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> "docker service logs -f visionai_backend"
```

### Rollback Deployment
```bash
chmod +x scripts/rollback.sh
./scripts/rollback.sh
```

### Update Secrets
```bash
echo "new_secret_value" | ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> \
  "docker secret create openai_api_key_v2 -"

# Update service to use new secret
ssh -i visionai-swarm-key.pem ubuntu@<manager_ip> \
  "docker service update --secret-rm openai_api_key --secret-add openai_api_key_v2 visionai_backend"
```

## Zero-Downtime Deployment Process

When you push to main:

1. **Build Phase**: GitHub Actions builds new Docker images
2. **Push Phase**: Images pushed to ECR with new tag
3. **Deploy Phase**: 
   - Stack deploy command updates service definitions
   - Docker Swarm performs rolling update:
     - Stops 1 replica
     - Starts new replica with new image
     - Waits for health check
     - Repeats for next replica
4. **Verification**: Health checks ensure no downtime

## Troubleshooting

### Services not starting
```bash
# Check service errors
docker service ps visionai_backend --no-trunc

# Check container logs
docker service logs visionai_backend --tail 100
```

### Database connection issues
- Verify MongoDB Atlas IP whitelist includes AWS IPs
- Check connection string in secrets
- Verify security group allows outbound traffic

### SSL certificate issues
- Ensure DNS records are correct
- Wait for certificate validation
- Check ACM console for status

### High memory usage
```bash
# Check resource usage
docker stats

# Scale down if needed
docker service scale visionai_automation=1
```

## Cost Optimization

- Use Reserved Instances for 1-year commitment (30-40% savings)
- Use Spot Instances for worker nodes (up to 70% savings)
- Enable auto-scaling based on CPU/memory metrics
- Use S3 lifecycle policies for old uploads
- Monitor and optimize MongoDB Atlas tier

## Security Best Practices

1. **Rotate secrets regularly** (every 90 days)
2. **Enable CloudWatch logs** for all services
3. **Set up AWS WAF** on ALB
4. **Enable VPC Flow Logs**
5. **Use AWS Systems Manager** for secure SSH access
6. **Enable MFA** on AWS account
7. **Regular security updates** on EC2 instances

## Backup Strategy

1. **MongoDB**: Atlas automatic backups (enabled by default)
2. **EFS**: AWS Backup daily snapshots
3. **Application state**: Docker volumes backed by EFS
4. **Configuration**: Git repository

## Next Steps

- Set up CloudWatch dashboards for monitoring
- Configure CloudWatch alarms for critical metrics
- Set up log aggregation with CloudWatch Logs
- Implement auto-scaling policies
- Set up staging environment
- Configure backup and disaster recovery
