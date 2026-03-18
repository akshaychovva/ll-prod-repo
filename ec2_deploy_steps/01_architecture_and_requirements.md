### 1. Production‑style EC2 architecture – big picture

This document explains the **target architecture** we’re aiming for on EC2.

We are moving from:

- **Single EC2 instance** with everything (app + DB) and a public IP.

To:

- A **multi‑AZ, load‑balanced, auto‑scaling, managed‑DB** architecture that is closer to real production.

---

### 1.1 High‑level architecture components

Here’s the target shape:

- **VPC (Virtual Private Cloud)** – your isolated network in AWS.
  - **Public subnets** (in 2+ AZs) – for the **Application Load Balancer (ALB)** and maybe bastion hosts.
  - **Private subnets** (in 2+ AZs) – for **EC2 app instances** and **RDS database**.

- **Application Load Balancer (ALB)**
  - Public endpoint (can be behind HTTPS and a domain).
  - Distributes incoming HTTP(S) requests across multiple EC2 instances in private subnets.

- **Auto Scaling Group (ASG) with EC2 instances**
  - EC2 instances running your containerized app (Docker + Docker Compose or baked AMI).
  - Minimum, desired, and maximum instance counts (e.g. 2–3 instances).
  - Health checks and automatic replacement of unhealthy instances.

- **Amazon RDS for Postgres**
  - Managed Postgres database in private subnets.
  - Automated backups, Multi‑AZ option, automated minor patching.

- **IAM roles and policies**
  - Instance role for EC2 to:
    - Access Bedrock.
    - Read secrets/parameters (DB passwords, configuration).
  - Roles for CI/CD pipelines and admins.

- **Secrets and config**
  - Use Systems Manager **Parameter Store** or **Secrets Manager** for:
    - Database credentials.
    - App secrets/API keys (if any).

- **Monitoring and logging**
  - CloudWatch Logs for all app logs (from EC2 instances).
  - CloudWatch metrics + alarms for CPU, latency, errors, DB health, etc.

---

### 1.2 How your app fits into this

Your existing components:

- Frontend: Streamlit.
- Backend: Flask API.
- Database: Postgres.
- LLM: AWS Bedrock (Anthropic models, etc.).

In the target architecture:

- **Frontend + backend**:
  - Packaged together on the **EC2 instances** (still using Docker Compose or a single orchestrated process per instance).
  - Served behind the **ALB**, which handles incoming traffic.

- **Database**:
  - Runs in **RDS Postgres** in private subnets (no direct public access).
  - EC2 instances connect using a **private endpoint** and credentials from Secrets Manager/Parameter Store.

- **Bedrock**:
  - Called by the backend using the **instance IAM role** (no hard‑coded keys).

---

### 1.3 Why this is more “production‑like”

Compared to a single EC2 instance with a public IP:

- **High availability**
  - With 2+ instances across **multiple AZs**, if one AZ or instance fails, others stay up.
  - RDS Multi‑AZ can also survive an AZ outage.

- **Scalability**
  - Auto Scaling can add more EC2 instances when load increases.
  - You can scale up/down based on CPU, requests per target, etc.

- **Security**
  - **No direct SSH** or RDP from the internet to app instances (you can use SSM Session Manager or a bastion host).
  - DB is not exposed to the internet.
  - Least‑privilege IAM roles for Bedrock and secrets.

- **Operations**
  - Logs and metrics are centralized in CloudWatch.
  - Easier to debug and monitor.

This is closer to what many real teams run in production (even if they use EKS instead of EC2 Auto Scaling).

---

### 1.4 What you need to be comfortable with (DevOps skill checklist)

As you go through the next docs, you will practice:

- **Networking**
  - VPCs, subnets (public vs private), routing tables, internet gateway, NAT gateway.
  - Security groups and how traffic flows through ALB → EC2 → RDS.

- **Compute**
  - Launch templates and Auto Scaling Groups.
  - User data scripts / bootstrap scripts.
  - Golden AMIs (optional, advanced).

- **Load balancing**
  - Application Load Balancers (ALBs).
  - Target groups and health checks.
  - Listeners and routing rules.

- **Databases**
  - RDS provisioning and configuration.
  - Parameter groups and security groups for DB.
  - Backups and retention.

- **IAM and security**
  - Roles for EC2, CI/CD, and admins.
  - Policies that allow Bedrock + SSM + secrets.

- **Automation**
  - Infrastructure as code (later you could express all of this in Terraform or CloudFormation).
  - CI/CD pipelines (GitHub Actions, CodePipeline).

- **Observability**
  - Logging patterns.
  - Metrics and alerts (CloudWatch).
  - Basic incident response flow.

Going through the concrete steps in the following files will give you a **solid mental model** and hands‑on experience with all of this.

---

### 1.5 Implementation order (what you will actually build)

Here is the **recommended order** to follow the rest of the files:

1. **Design and create VPC & networking**  
   → `02_networking_vpc_subnets_and_security_groups.md`

2. **Set up IAM roles and secrets**  
   → `03_iam_and_secrets_management.md`

3. **Create Auto Scaling Group + ALB for the app**  
   → `04_ec2_auto_scaling_and_load_balancer.md`

4. **Provision RDS Postgres and connect the app**  
   → `05_database_and_storage_strategy.md`

5. **Set up CI/CD pipeline and deployment flows**  
   → `06_ci_cd_and_deployment_strategy.md`

6. **Configure logging, metrics, and alerts**  
   → `07_observability_logging_and_alerting.md`

You can implement a **minimal version** of each step first, then iterate and harden as you gain confidence.

