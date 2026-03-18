### Production‑style EC2 deployment – roadmap

This folder is the **“next level”** after your simple single‑EC2 deployment in `ec2_deply/`.

Goal: walk you through a **more production‑like architecture on EC2**, step by step, with explanations, so you start thinking like a **DevOps/Cloud engineer**:

- Highly available (multi‑AZ) setup.
- Load balancer in front of your app.
- Auto Scaling (scale out/in EC2 instances).
- Managed database (RDS) with backups.
- Centralized logs, metrics, alerts.
- Safer networking, IAM, and secrets.
- Basic CI/CD for repeatable deployments.

> This is still “EC2‑centric” (not EKS yet), but the same thinking will help you when you move to Kubernetes.

---

### How to use this folder

Read the files **in order**. Each one:

- Explains the **concepts**.
- Then gives you **concrete steps** you can actually follow in AWS.

---

### Files in this folder

- `01_architecture_and_requirements.md`  
  Big‑picture production architecture: VPC, public/private subnets, ALB, Auto Scaling Group, RDS, and how your app fits in.

- `02_networking_vpc_subnets_and_security_groups.md`  
  Design and create a basic production VPC layout: multi‑AZ subnets, routing, and security groups for ALB, EC2, and RDS.

- `03_iam_and_secrets_management.md`  
  IAM roles/policies for EC2 and admins, how to avoid hard‑coded secrets, and how to use Parameter Store/Secrets Manager for DB and app config.

- `04_ec2_auto_scaling_and_load_balancer.md`  
  Build a launch template, an Auto Scaling Group, and an Application Load Balancer (ALB) that distributes traffic across EC2 instances.

- `05_database_and_storage_strategy.md`  
  Use Amazon RDS for Postgres, set up subnets, security, backups, and connect your app to it instead of a containerized DB.

- `06_ci_cd_and_deployment_strategy.md`  
  Push app images to ECR, and create a simple CI/CD flow (GitHub Actions / CodePipeline) plus strategies like rolling and blue/green.

- `07_observability_logging_and_alerting.md`  
  Centralized logs (CloudWatch Logs), metrics (CloudWatch), basic dashboards and alarms, and simple runbooks for incidents.

---

### Additional deep‑dive (CI/CD)

If you want a very beginner‑friendly, highly detailed CI/CD and deployment walkthrough (including exactly how EC2 instances pull images and how deployments roll out), use:

- `ci_cd_deploy/` (folder at repo root)

You don’t have to build everything in one day. Work through each file, apply the steps in your AWS account, and you will gradually think and work much more like a **production DevOps engineer**.

