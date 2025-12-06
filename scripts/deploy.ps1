<#
.SYNOPSIS
    Vision.AI Single Node Deployment Script for Windows
    Deploys to 13.51.158.58

.DESCRIPTION
    Automates the deployment process:
    1. Checks/Prompts for AWS Credentials
    2. Builds Docker Images
    3. Pushes to ECR
    4. Deploys to Remote Swarm Cluster
#>

$ErrorActionPreference = "Stop"
$ServerIP = "13.51.158.58"
$Region = "eu-north-1"
$KeyFile = "visionai.pem"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Vision.AI Deployment (Windows)" -ForegroundColor Green
Write-Host "Target: $ServerIP" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green


if (-not $RegistryUri) {
    Write-Host "No ECR repositories found. Creating one..." -ForegroundColor Yellow
    Write-Host "Creating repository: visionai"
    Invoke-Aws ecr create-repository --repository-name visionai --region $Region | Out-Null
    
    # Fetch URI again
    $RegistryUri = Invoke-Aws ecr describe-repositories --region $Region --query 'repositories[0].repositoryUri' --output text
}

# Extract registry base URL (e.g., 12345.dkr.ecr.eu-north-1.amazonaws.com)
$RegistryBase = $RegistryUri.Split("/")[0]
$env:ECR_REGISTRY = $RegistryBase

Write-Host "Logging in to ECR ($RegistryBase)..."
Invoke-Aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $RegistryBase

# 4. Build and Push
Write-Host "`n[3/4] Building and Pushing Images..." -ForegroundColor Yellow
$Images = @("visionai-backend", "visionai-frontend", "visionai-automation")

# Build
docker compose -f docker-compose.swarm.yml build

# Tag and Push
foreach ($Img in $Images) {
    # Img is like visionai-backend
    # We want visionai:backend-latest
    $Service = $Img.Replace("visionai-", "")
    $TargetTag = "$RegistryBase/visionai:$Service-latest"
    
    Write-Host "Pushing $TargetTag..."
    docker tag "$Img`:latest" $TargetTag
    docker push $TargetTag
}

# 5. Deploy to Server
Write-Host "`n[4/4] Deploying to Server..." -ForegroundColor Yellow

# Get Login Password LOCALLY to avoid needing AWS CLI/Creds on server
Write-Host "Generating auth token for remote server..."
$DockerPass = Invoke-Aws ecr get-login-password --region $Region

# Prepare Secrets Variables
$OpenAIKey = $EnvVars["OPENAI_API_KEY"]
$StripeKey = $EnvVars["STRIPE_SECRET_KEY"]
$JwtSecret = $EnvVars["JWT_SECRET_KEY"]
$GoogleId = $EnvVars["GOOGLE_CLIENT_ID"]
$GoogleSecret = $EnvVars["GOOGLE_CLIENT_SECRET"]

# Copy stack file
scp -o StrictHostKeyChecking=no -i $KeyFile "docker-compose.swarm.yml" "ubuntu@$($ServerIP):~/"

# Run deployment command
# We pass the password securely via stdin or env var
$DeployCmd = @"
    export ECR_REGISTRY=$RegistryBase
    export OPENAI_API_KEY='$OpenAIKey'
    export STRIPE_API_KEY='$StripeKey'
    export JWT_SECRET='$JwtSecret'
    export GOOGLE_CLIENT_ID='$GoogleId'
    export GOOGLE_CLIENT_SECRET='$GoogleSecret'
    
    # Helper to create secret
    create_secret() {
        name=\$1
        value=\$2
        if [ ! -z "\$value" ]; then
            if ! docker secret ls | grep -q "\$name"; then
                echo "Creating secret: \$name"
                printf "%s" "\$value" | docker secret create \$name -
            else
                echo "Secret \$name exists (skipping)"
            fi
        fi
    }
    
    # Create secrets
    create_secret "OPENAI_API_KEY" "\$OPENAI_API_KEY"
    create_secret "STRIPE_SECRET_KEY" "\$STRIPE_API_KEY"
    create_secret "JWT_SECRET_KEY" "\$JWT_SECRET"
    create_secret "GOOGLE_CLIENT_ID" "\$GOOGLE_CLIENT_ID"
    create_secret "GOOGLE_CLIENT_SECRET" "\$GOOGLE_CLIENT_SECRET"

    echo "$DockerPass" | docker login --username AWS --password-stdin $RegistryBase
    docker compose -f docker-compose.swarm.yml pull
    docker stack deploy --compose-file docker-compose.swarm.yml visionai
    docker image prune -f
"@

ssh -o StrictHostKeyChecking=no -i $KeyFile "ubuntu@$($ServerIP)" $DeployCmd

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Triggered!" -ForegroundColor Green
Write-Host "Check status: https://webtestingdomain.online"
Write-Host "Monitor logs: ssh -i $KeyFile ubuntu@$($ServerIP) 'docker service logs -f visionai_backend'"
Write-Host "========================================" -ForegroundColor Green
