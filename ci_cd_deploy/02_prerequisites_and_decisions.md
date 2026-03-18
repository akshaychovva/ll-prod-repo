### 2. Prerequisites and one‑time decisions

This document is intentionally “slow”: it prevents you from building things in the wrong order.

---

### 2.1 Prerequisites checklist

You need:

- **An AWS account** and the ability to create:
  - ECR repositories,
  - IAM roles,
  - EC2/ASG/ALB,
  - SSM parameters,
  - (Optional) RDS.

- **A GitHub repository** for this code (private or public).

- **AWS CLI installed** on your local machine (for quick tests).

- **Bedrock enabled** in the chosen region and model access granted (see `aws_bedrock_setup.md`).

---

### 2.2 Choose a single AWS region and stick to it

Pick one region and use it for everything:

- Bedrock model access
- ECR repositories
- VPC / ALB / ASG
- SSM Parameter Store
- RDS

Example: `us-east-1`.

Why:

- ECR images are region‑specific.
- Bedrock access is region‑specific.
- Keeping it consistent avoids “it works in one region but not another” confusion.

---

### 2.3 Decide: “clone on EC2” vs “pull images from ECR”

To be production‑ready, use:

- **Pull images from ECR** on instance boot.

This means:

- Your EC2 user data script will **NOT** build images.
- It will:
  - log into ECR,
  - pull images by tag,
  - start containers.

Why:

- Faster and consistent boot.
- Easier rollback (just change tag).

We will build the CI/CD docs assuming ECR‑pull is your main path.

---

### 2.4 Decide: how will you “tell EC2 which version to run”?

You need one central place to store “current production version”.

Two common approaches:

#### Option A (recommended for learning): store an image tag in SSM Parameter Store

- Create a parameter like:
  - `/prod/llm-app/release/imageTag`
- When you deploy:
  - CI updates that parameter to the new tag (e.g. commit SHA).
- On EC2 boot:
  - user data reads that parameter and pulls images with that tag.

Why this is great for learning:

- Easy to update without rebuilding templates.
- Rollback is just changing one parameter.

#### Option B: bake the tag into a Launch Template version

- Create a new Launch Template version per release with the tag inside user data.
- Update ASG to use that version.

Why it’s okay but heavier:

- More manual clicks unless you automate via IaC.

We will use **Option A** in later steps.

---

### 2.5 Naming conventions (keep it consistent)

Pick names early so you don’t get confused later.

Example:

- ECR repos:
  - `llm-app-backend`
  - `llm-app-frontend`
- SSM parameters:
  - `/prod/llm-app/db/*`
  - `/prod/llm-app/release/imageTag`
- ASG:
  - `prod-llm-app-asg`
- ALB:
  - `prod-llm-alb`
- Target group:
  - `prod-llm-app-tg`

---

### 2.6 Cost warning (important)

This “production‑style EC2” path can cost money, especially:

- NAT gateways,
- ALB,
- RDS,
- multiple EC2 instances.

If you want to learn cheaply:

- Start with:
  - 1 NAT gateway (not per AZ),
  - 2 small EC2 instances in ASG,
  - no RDS Multi‑AZ at first,
  - stop/tear down resources when idle.

---

### 2.7 Summary (decisions you should lock now)

By the time you move to the next file, you should have:

- **Region** chosen.
- **GitHub repo** created for this project.
- Decision: **ECR pull** on EC2 boot.
- Decision: “current version” stored in **SSM parameter** `/prod/llm-app/release/imageTag`.

Next: `03_create_ecr_repos.md`.

