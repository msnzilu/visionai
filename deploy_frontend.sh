#!/bin/bash

# Deploy frontend to remote server
# Usage: ./deploy_frontend.sh

set -e  # Exit on any error

# Configuration
PEM_KEY="visionai.pem"
SOURCE_DIR="G:/Desktop/visionai/frontend"
REMOTE_USER="ubuntu"
REMOTE_HOST="13.51.158.58"
TEMP_DIR="/tmp/frontend"
DEST_DIR="/var/www/visionai"

echo "Starting frontend deployment..."

# Step 1: Copy files to remote server's temp directory
echo "Copying files to remote server..."
scp -i "$PEM_KEY" -r "$SOURCE_DIR"/* "$REMOTE_USER@$REMOTE_HOST:$TEMP_DIR/"

# Step 2: SSH into server and move files to final destination
echo "Moving files to final destination..."
ssh -i "$PEM_KEY" "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
sudo cp -r /tmp/frontend/* /var/www/visionai/
echo "Files deployed successfully!"
EOF

echo "Deployment complete!"