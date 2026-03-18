### 6. CI/CD and deployment strategy

To be “production‑ready” you must be able to:

- Build and test the app automatically.
- Build/push container images to a registry.
- Deploy updates to EC2 instances **consistently and safely**.

We’ll outline a simple but realistic CI/CD flow using:

- **GitHub Actions** (or similar) for CI/CD.
- **Amazon ECR** for container images.
- Your existing **ASG + Launch Template** for deployment.

---

### 6.1 Container image registry (ECR)

First, choose where your images live:

- **Amazon ECR** is natural when running in AWS.

Steps (high level):

1. In AWS Console, open **ECR**.
2. Create two repositories:
   - `llm-app-backend`
   - `llm-app-frontend`
3. Configure IAM for your CI system (GitHub Actions) to:
   - Authenticate to ECR.
   - Push/pull images.

You will end up tagging images like:

```text
<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-backend:<git-sha-or-version>
<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-frontend:<git-sha-or-version>
```

---

### 6.2 Build and push images in CI (GitHub Actions example)

In your GitHub repo, create a workflow file (for example `.github/workflows/build-and-push.yml`) that:

1. Triggers on pushes to `main` (and/or pull requests).
2. Checks out the code.
3. Logs into ECR using AWS credentials (via OIDC or access keys).
4. Builds Docker images for backend and frontend.
5. Pushes them to ECR with tags like:
   - `latest`
   - `<git-sha>`

Conceptually:

```yaml
name: Build and push images

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/GithubActionsECRRole
          aws-region: <your-region>

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push backend
        run: |
          BACKEND_REPO="<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-backend"
          TAG=${GITHUB_SHA}
          docker build -t $BACKEND_REPO:$TAG -f backend/Dockerfile .
          docker push $BACKEND_REPO:$TAG

      - name: Build and push frontend
        run: |
          FRONTEND_REPO="<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-frontend"
          TAG=${GITHUB_SHA}
          docker build -t $FRONTEND_REPO:$TAG -f frontend/Dockerfile .
          docker push $FRONTEND_REPO:$TAG
```

You’ll adapt this to your exact repo structure and policies.

---

### 6.3 How EC2 instances pull the new images

With images in ECR, update your **user data / startup script** in the Launch Template so that instead of:

- `git clone` + `docker compose up --build`

You do:

- `docker compose up` with `image:` pointing to ECR, or
- `docker run` directly with ECR images.

Example snippet in user data (conceptual):

```bash
BACKEND_REPO="<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-backend"
FRONTEND_REPO="<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-frontend"
TAG="<git-sha-or-latest>"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "<account-id>.dkr.ecr.$REGION.amazonaws.com"

docker pull $BACKEND_REPO:$TAG
docker pull $FRONTEND_REPO:$TAG

# Start containers with those images (via docker compose or docker run)
```

Now when you **release a new version**:

- Build/push new images with the new tag.
- Update your Launch Template (or parameter) to reference the new tag.
- Roll out changes via the Auto Scaling Group.

---

### 6.4 Deployment strategies with ASG + ALB

Common production patterns:

- **Rolling update** (simple with ASG):
  - Create a new **Launch Template version** that points to the new image tag.
  - Update the ASG to use that Launch Template version.
  - Gradually replace instances:
    - New instances start with new version.
    - Old ones terminate once new ones are healthy.

- **Blue/Green** (safer but more complex):
  - Run **two ASGs** (blue and green) behind the ALB:
    - Blue = current production.
    - Green = new version.
  - Test green via a separate target group / path / DNS.
  - When happy, switch ALB routing or DNS from blue to green.

For starting out, **rolling update with ASG** is perfectly fine:

1. Update Launch Template (new image tag).
2. Update ASG to use that template version.
3. Optionally, use an ASG **instance refresh**:
   - It gradually recycles instances and respects ALB health checks.

---

### 6.5 CI/CD pipeline outline

Your end‑to‑end CI/CD picture can look like this:

1. **Developer pushes to main**.
2. **CI pipeline**:
   - Runs tests (unit/integration).
   - Builds Docker images.
   - Pushes images to ECR.
   - Optionally updates a manifest or parameter that stores the **current image tag**.
   - Optionally triggers a **CD step** (manual approval or automatic) that:
     - Updates Launch Template version or ASG config.
     - Initiates an ASG instance refresh (rolling deployment).

3. **ASG + ALB**:
   - Launch new instances with new images.
   - Route traffic only to healthy instances.

4. **Observability**:
   - CloudWatch alarms and dashboards show if the new version is healthy.

---

### 6.6 Manual “poor‑man’s” deployment (for learning)

Before building full CI/CD, you can practice manual steps:

1. Build/push images from your laptop (one time).
2. Update user data / Launch Template to use the new tags.
3. In the ASG:
   - Manually **terminate one instance at a time**:
     - The ASG will launch a new one using the latest Launch Template.
     - ALB health checks ensure only healthy ones receive traffic.

This will help you understand the moving pieces before you automate them.

---

### 6.7 Summary – CI/CD mindset

With this setup you:

- Treat your deploys as **repeatable operations**, not manual EC2 tinkering.
- Use **ECR** for versioned images.
- Let **ASG + ALB** handle rolling out new instances.
- Use **GitHub Actions** (or similar) to automate builds and releases.

This is the core of a production DevOps workflow. Next, in `07_observability_logging_and_alerting.md`, you’ll add the remaining piece: **visibility** into what’s happening so you can operate this system confidently.

