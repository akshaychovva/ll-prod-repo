### CI/CD + EC2 deployment (very detailed)

This folder is a **beginner‑friendly, step‑by‑step CI/CD guide** that answers:

- **What** to do (exact steps)
- **Why** you do it (concepts)
- **How** it connects to EC2 Auto Scaling and Load Balancing

It is designed to remove the confusion around:

- “When do I launch EC2?”
- “Do I clone the repo on EC2 or pull images from ECR?”
- “How does a GitHub push become a safe production deployment?”

---

### Recommended approach (production‑style, still simple)

- Build Docker images in CI
- Push images to **Amazon ECR**
- Deploy by updating **Launch Template/User Data** (or a parameter storing image tag)
- Roll out safely using **ASG Instance Refresh** (rolling deployment behind ALB health checks)

This avoids SSH manual steps and makes deployments repeatable.

---

### Files in this folder (read in order)

- `01_ci_cd_big_picture.md`  
  The end‑to‑end pipeline in plain language: source → build → registry → deploy → observe → rollback.

- `02_prerequisites_and_decisions.md`  
  Simple decisions you must make once: region, GitHub repo, naming, “clone vs ECR pull”, and budget/cost notes.

- `03_create_ecr_repos.md`  
  Create ECR repositories for backend and frontend, explain tags and versioning.

- `04_github_actions_to_ecr_with_oidc.md`  
  The best‑practice way to authenticate GitHub Actions to AWS (OIDC) and push images to ECR.

- `05_ec2_bootstrap_pull_from_ecr.md`  
  Exactly what runs on EC2 at boot: user data script that pulls images from ECR, fetches config from SSM, starts containers.

- `06_deploy_to_asg_instance_refresh.md`  
  How to roll out a new version safely using Launch Template versions + ASG Instance Refresh + ALB health checks.

- `07_optional_blue_green.md`  
  A clearer “safer than rolling” strategy (blue/green) explained step by step.

- `08_troubleshooting_and_rollbacks.md`  
  How to debug failures (CI failures, ECR auth, boot issues, health checks) and how to roll back quickly.

