# Quick Start - Single Node AWS Deployment

Deploy Vision.AI to your existing AWS instance (`13.51.158.58`).

# Quick Start - Single Node AWS Deployment

Deploy Vision.AI to your existing AWS instance (`13.51.158.58`).

## Option 1: GitHub Actions (Recommended)

**1. Create ECR Repository (AWS Console)**
   - Go to **Amazon ECR** -> **Repositories**.
   - Create **1** repository named: `visionai`
   - Copy the URI (e.g., `1234.dkr.ecr.eu-north-1.amazonaws.com/visionai`).
   - The part BEFORE `/visionai` is your `ECR_REGISTRY`.

**2. Add GitHub Secrets**
   - Add all secrets listed in `docs/GITHUB_SECRETS.md`.
   - **Important**: Add `SWARM_SSH_PRIVATE_KEY` (content of `visionai.pem`).

**3. Deploy**
   - Push your code to the `main` branch.
   - Go to **Actions** tab in GitHub to watch the deployment.

---

## Option 2: Manual Windows Script (Alternative)

If you prefer running from your machine:
```powershell
./scripts/deploy.ps1
```

### Step 1: Configure DNS
Create an **A Record** for `webtestingdomain.online` pointing to `13.51.158.58`.

### Step 2: Prepare Server (First Time Only)
```bash
# Upload and run setup script
scp -i visionai.pem aws/setup-single-node.sh ubuntu@13.51.158.58:~/
ssh -i visionai.pem ubuntu@13.51.158.58 "chmod +x setup-single-node.sh && ./setup-single-node.sh"
```

### Step 3: Deploy (Mac/Linux)
```bash
export SSH_KEY="visionai.pem"
./scripts/deploy-single.sh
```

### Verification
Visit https://webtestingdomain.online
