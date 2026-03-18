### 5. EC2 bootstrap: pull from ECR and start the app (no manual SSH)

This is the missing link for many beginners:

- “CI built the images and pushed to ECR… now what?”

Answer:

- Your **EC2 instances** (managed by ASG) will automatically:
  - read the “current version tag” from SSM,
  - pull that tag from ECR,
  - start containers.

You do not SSH and run `docker compose` manually for every deploy.

---

### 5.1 What you must have ready before this step

You should already have:

- ECR repositories created (Step 3).
- GitHub Actions pushing images to ECR (Step 4).
- A VPC + private app subnets + security groups (from `ec2_deploy_steps/02...`).
- An IAM role for EC2 app instances with permissions:
  - `AmazonSSMManagedInstanceCore`
  - Bedrock invoke permissions
  - SSM parameter read permissions
  - ECR pull permissions

Important:

- EC2 instances need ECR pull permissions, typically actions like:
  - `ecr:GetAuthorizationToken`
  - `ecr:BatchGetImage`
  - `ecr:GetDownloadUrlForLayer`
  - `ecr:BatchCheckLayerAvailability`

---

### 5.2 Create a “current release tag” parameter in SSM

We store which version production should run in one parameter.

In AWS Console:

1. Open **Systems Manager → Parameter Store**.
2. Create parameter:
   - Name: `/prod/llm-app/release/imageTag`
   - Type: `String`
   - Value: (start with something simple; later CI updates it)
     - Example: a known commit SHA that exists in ECR

Why:

- EC2 user data can read this value at boot time.
- Deployments and rollbacks become “change one parameter”.

---

### 5.3 Decide how instances start your app: docker compose file on instance

Your EC2 instances need a way to start containers consistently.

Two practical options:

#### Option A (common): ship a small “runtime bundle” repo and use docker compose

- You keep a minimal folder in Git (or S3) that contains:
  - a `docker-compose.yml` that references ECR images (no build).
  - a `.env` template (optional).
  - a `systemd` unit file (optional).

Pros:

- Very flexible and simple to understand.

Cons:

- Still needs a small “clone or download” step for the compose file.

#### Option B: user data runs `docker run ...` directly

Pros:

- No compose file needed.

Cons:

- More commands, harder to maintain as the app grows.

For learning, Option A is usually easiest.

---

### 5.4 Launch Template user data: full “pull from ECR and run” example

In your Launch Template, in **User Data**, use a script like the below.

What it does:

1. Installs Docker and Compose.
2. Reads DB config and the release tag from SSM.
3. Logs into ECR.
4. Pulls images by tag.
5. Starts containers.

Example (Amazon Linux 2023 style; replace placeholders):

```bash
#!/bin/bash
set -euo pipefail

REGION="us-east-1"
ACCOUNT_ID="123456789012"

BACKEND_REPO="llm-app-backend"
FRONTEND_REPO="llm-app-frontend"

APP_PATH="/prod/llm-app"

dnf update -y
dnf install -y docker awscli docker-compose-plugin
systemctl enable docker
systemctl start docker

# Fetch configuration (DB + release tag)
DB_HOST=$(aws ssm get-parameter --name "$APP_PATH/db/host" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_PORT=$(aws ssm get-parameter --name "$APP_PATH/db/port" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_NAME=$(aws ssm get-parameter --name "$APP_PATH/db/name" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_USER=$(aws ssm get-parameter --name "$APP_PATH/db/user" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_PASSWORD=$(aws ssm get-parameter --name "$APP_PATH/db/password" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
IMAGE_TAG=$(aws ssm get-parameter --name "$APP_PATH/release/imageTag" --query "Parameter.Value" --output text --region "$REGION")

# Login to ECR
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

BACKEND_IMAGE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${BACKEND_REPO}:${IMAGE_TAG}"
FRONTEND_IMAGE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${FRONTEND_REPO}:${IMAGE_TAG}"

docker pull "$BACKEND_IMAGE"
docker pull "$FRONTEND_IMAGE"

# Create a runtime docker-compose.yml on the instance (simple approach)
mkdir -p /opt/llm-app
cat > /opt/llm-app/docker-compose.yml <<EOF
services:
  backend:
    image: ${BACKEND_IMAGE}
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - AWS_REGION=${REGION}
    ports:
      - "8000:8000"

  frontend:
    image: ${FRONTEND_IMAGE}
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8501:8501"
    depends_on:
      - backend
EOF

cd /opt/llm-app
docker compose up -d
```

Important notes:

- This example assumes your containers listen on ports 8000 and 8501.
  - If your actual backend listens on a different port, change it here.
- In a production ALB setup, you may not want to expose ports directly on the instance to the internet:
  - Only ALB should talk to instances.
  - Security groups handle that.

---

### 5.5 Where EC2 “launch” happens now

After your Launch Template is updated:

- If you already have an ASG:
  - Trigger an **Instance Refresh** (next file) to replace old instances.

If you’re creating the ASG for the first time:

- When you set **Desired capacity = 2**, ASG will:
  - Launch 2 EC2 instances automatically.
  - Each one runs the user data above.

So you do not launch EC2 manually.

---

### 5.6 Summary

You now have a clear, production‑style model:

- CI builds images → ECR
- “Current version” lives in SSM parameter
- EC2 instances boot → read SSM → pull from ECR → start containers
- Deployments become “change version pointer + refresh instances”

Next: `06_deploy_to_asg_instance_refresh.md` to do safe rolling deployments behind the ALB.

