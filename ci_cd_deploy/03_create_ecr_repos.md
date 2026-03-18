### 3. Create ECR repositories (where your Docker images live)

This step creates a place in AWS to store your container images so EC2 instances can pull them reliably.

---

### 3.1 What ECR is (in simple words)

- **ECR (Elastic Container Registry)** is like “DockerHub inside AWS”.
- It stores versioned images:
  - backend image
  - frontend image
- Your CI pipeline will push images there.
- Your EC2 instances will pull images from there.

Why it matters:

- Your servers should not build images in production.
- They should download an already built, tested artifact.

---

### 3.2 Create repositories (AWS Console)

1. Open AWS Console → search **ECR** → open **Elastic Container Registry**.
2. Go to **Repositories**.
3. Click **Create repository**.

Create two repositories:

#### Backend repo

- **Repository name**: `llm-app-backend`
- **Visibility**: Private
- **Tag immutability**: (recommended) Enable immutability if you want stricter discipline.
  - If you enable immutability, you should never “reuse” tags like `latest`.
  - For learning, you can keep it mutable.

Click **Create repository**.

#### Frontend repo

- **Repository name**: `llm-app-frontend`
- Same options as above.

Click **Create repository**.

Now you will have two repository URIs like:

```text
<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-backend
<account-id>.dkr.ecr.<region>.amazonaws.com/llm-app-frontend
```

Write these down. You will paste them into:

- GitHub Actions workflow (push step)
- EC2 user data (pull step)

---

### 3.3 Image tagging strategy (very important)

Use two kinds of tags:

- **Immutable tag**: commit SHA (best)
  - Example: `a1b2c3d4...`
  - This is exactly one build, forever.

- **Optional “channel” tag**: `latest` or `prod`
  - Easy to understand, but mutable.
  - If you’re learning, it’s okay, but production teams prefer immutable tags for safety.

Recommended for you:

- Always push the SHA tag.
- Optionally also push `latest`.

Later, your release parameter `/prod/llm-app/release/imageTag` should be set to the **SHA tag**.

---

### 3.4 Quick local test (optional)

If you want to confirm you can log into ECR from your machine:

1. Configure AWS CLI (`aws configure`) and region.
2. Run:

```bash
aws ecr get-login-password --region <your-region> \
  | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<your-region>.amazonaws.com
```

If login succeeds, your local machine can authenticate to ECR.

---

### 3.5 Summary

You now have:

- An ECR repo for backend.
- An ECR repo for frontend.
- A plan for tagging images safely.

Next: `04_github_actions_to_ecr_with_oidc.md` to connect GitHub Actions to AWS (without storing long‑lived AWS keys in GitHub).

