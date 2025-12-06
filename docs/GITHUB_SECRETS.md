# GitHub Actions Secrets Configuration

Configure these secrets in your GitHub repository for automated CI/CD deployment.

## Location

Repository → Settings → Secrets and variables → Actions → New repository secret

## Required Secrets

### AWS Credentials

**How to get them:**
1. Go to AWS Console -> **IAM** -> **Users** -> Create User (e.g., `github-deployer`).
2. Attach policies: `AmazonEC2FullAccess` and `AmazonEC2ContainerRegistryFullAccess`.
3. Create User -> Click on user -> **Security credentials** tab.
4. **Create access key** (Select CLI use case).
5. Copy the **Access Key ID** and **Secret Access Key**.

**AWS_ACCESS_KEY_ID**
```
AKIA...
```

**AWS_SECRET_ACCESS_KEY**
```
wJalr... (cannot be viewed again after creation)
```

### ECR Configuration

**ECR_REGISTRY**
```
Your ECR registry URL
Get from: infrastructure-summary.txt or AWS Console
```

### Swarm Manager Access

**SWARM_MANAGER_HOST**
```
13.51.158.58
```

**SWARM_SSH_PRIVATE_KEY**
```
Contents of visionai.pem file
Copy entire file including:
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

### Application Secrets

**OPENAI_API_KEY**
```
sk-...
```

**STRIPE_API_KEY**
```
sk_live_...
```

**JWT_SECRET**
```
A long random string
```

**GOOGLE_OAUTH_CLIENT_ID**
```
...
```

**GOOGLE_OAUTH_CLIENT_SECRET**
```
...

---

## DEPRECATED / NOT NEEDED

*(These are handled locally on the server now)*

- `MONGO_USER`
- `MONGO_PASSWORD`
- `MONGO_HOST`
- `MONGO_DB`
- `REDIS_HOST`
- `NFS_SERVER`

## How to Add Secrets

### Using GitHub Web Interface

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter **Name** and **Value**
6. Click **Add secret**
