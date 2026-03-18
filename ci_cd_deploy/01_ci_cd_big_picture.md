### 1. CI/CD big picture (what happens from code → production)

This page gives you the “movie trailer” view of the pipeline, so every later step makes sense.

---

### 1.1 The problem CI/CD solves

If you deploy by SSH’ing into servers and running commands manually:

- It works for demos,
- but in production it causes problems:
  - People make mistakes (wrong commands, wrong server).
  - Nobody knows exactly what version is running.
  - Rollbacks are slow and risky.
  - The same change behaves differently on different servers.

CI/CD makes deployments:

- **Repeatable** (same steps every time),
- **Auditable** (you know which commit is running),
- **Safer** (health checks, gradual rollout),
- **Faster** (push code → pipeline deploys).

---

### 1.2 The production‑style flow we want

We will implement this simple production flow:

1. **Developer pushes code** to GitHub (`main` branch).
2. **CI** (GitHub Actions) runs:
   - Lint/tests (basic checks).
   - Build Docker images:
     - backend image
     - frontend image
   - Tag images with:
     - the commit SHA (immutable tag)
     - optionally `latest` (mutable tag)
3. CI **pushes images** to **Amazon ECR**.
4. CI triggers **CD**:
   - Update a “release pointer” to the new image tag, for example:
     - Update SSM Parameter Store `/prod/llm-app/release/imageTag` to the new SHA, OR
     - Create a new Launch Template version that contains the tag (more manual).
5. **Auto Scaling Group** rolls out:
   - ASG launches new instances that boot using User Data.
   - During boot they:
     - fetch config/secrets from SSM
     - pull images from ECR
     - start containers
   - ALB health checks ensure only healthy instances receive traffic.
6. **Observability** watches the rollout:
   - ALB 5xx errors, latency, logs, etc.
7. If something goes wrong:
   - **Rollback** by setting the release pointer back to the previous tag
   - Trigger another instance refresh to revert.

Key idea:

- Your “production servers” are **not snowflakes**.
- They are replaceable and are rebuilt automatically from a template.

---

### 1.3 Where EC2 “launch” happens in this flow

In production, you don’t typically click **“Launch instance”** to deploy a new version.

Instead:

- You define “how to build an instance” (Launch Template + User Data).
- You tell ASG “I want N instances” (Desired capacity).
- During deployment you tell ASG “replace instances gradually” (Instance Refresh).

That’s when EC2 instances are launched:

- On initial ASG creation,
- On scale‑out events,
- On rolling deployments (instance refresh),
- When AWS replaces unhealthy instances.

---

### 1.4 Two ways to get your app onto the instance (choose one)

There are two common approaches:

#### A) “Clone repo on boot”

- User Data does:
  - `git clone ...`
  - `docker compose up --build`

Pros:

- Very easy to understand.

Cons:

- Slower and less reliable at scale.
- Builds images on every instance (wastes time and cost).
- More variance (depends on network at boot).

#### B) “Pull prebuilt images from ECR” (recommended)

- CI builds images once and pushes to ECR.
- User Data does:
  - `docker pull <ecr-image>:<tag>`
  - `docker compose up -d` (or `docker run ...`)

Pros:

- Faster instance boot (no build step on servers).
- Consistent and reproducible (image is immutable).
- Standard production pattern.

Cons:

- Slightly more setup (ECR + CI auth).

For becoming production‑ready, prefer **B**.

---

### 1.5 Summary

After you complete this folder, you will have:

- A working CI pipeline that produces versioned artifacts (Docker images).
- A clean CD mechanism that updates what production runs.
- A safe rollout method using ASG + ALB health checks.
- A clear rollback path.

Next: `02_prerequisites_and_decisions.md` to lock down a few choices (region, repo, naming) before creating ECR and workflows.

