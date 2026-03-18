### 2. Networking – VPC, subnets, and security groups

This document turns the architecture into a **concrete network design** and then into **step‑by‑step actions** in AWS.

---

### 2.1 Target network design

We’ll create a **production‑style VPC** with:

- **VPC** – e.g. `10.0.0.0/16`.
- **Public subnets** in 2 AZs:
  - Example: `10.0.1.0/24` (AZ a), `10.0.2.0/24` (AZ b).
  - Hosts **ALB** (and optionally a bastion host).
  - Internet access via **Internet Gateway (IGW)**.
- **Private app subnets** in 2 AZs:
  - Example: `10.0.11.0/24` (AZ a), `10.0.12.0/24` (AZ b).
  - Hosts **EC2 app instances** in Auto Scaling Group.
  - Outbound internet via **NAT Gateway** (for updates, Bedrock SDK, etc.).
- **Private DB subnets** in 2 AZs:
  - Example: `10.0.21.0/24` (AZ a), `10.0.22.0/24` (AZ b).
  - Hosts **RDS Postgres**.
  - No direct internet access; only via app and management paths.

Security groups:

- **ALB SG (`sg-alb`)**
  - Inbound: HTTP/HTTPS from the internet.
  - Outbound: to EC2 app SG.

- **App SG (`sg-app`)**
  - Inbound: HTTP from ALB SG only.
  - Outbound: to RDS SG, to Bedrock endpoints, to SSM, etc.

- **DB SG (`sg-db`)**
  - Inbound: Postgres (5432) from App SG only.
  - Outbound: minimal.

This is a standard pattern: **public ALB → private EC2 → private RDS**.

---

### 2.2 Create a VPC with subnets (AWS Console)

1. In the AWS Console, go to **VPC** service.
2. Click **“Create VPC”**.
3. Choose **“VPC and more”** (the wizard that creates subnets and gateways).

Fill the form with something like:

- **Name tag auto‑generation**: `prod-llm-vpc`.
- **IPv4 CIDR block**: `10.0.0.0/16`.
- **Number of Availability Zones (AZs)**: 2.
- **Number of public subnets**: 2.
- **Number of private subnets**: 4 (2 for app, 2 for DB – we’ll categorize them).
- **NAT gateways**: 1 per AZ (2 total) or start with 1 to reduce cost.
- **VPC endpoints**: optional for now (you can add SSM, S3, etc. later).

Click **Create VPC**.

The wizard will:

- Create the VPC.
- Create public and private subnets.
- Attach an Internet Gateway.
- Create routing tables with proper routes.
- Optionally create NAT gateways.

Make a note of:

- VPC ID (e.g. `vpc-xxxx`).
- Subnet IDs and which ones are public/private.

You may want to **rename subnets** with clear names, for example:

- `prod-llm-public-a`, `prod-llm-public-b`.
- `prod-llm-private-app-a`, `prod-llm-private-app-b`.
- `prod-llm-private-db-a`, `prod-llm-private-db-b`.

You can adjust tags later to categorize which private subnets you will use for app vs DB.

---

### 2.3 Confirm Internet and NAT routing

Check route tables:

1. In the VPC console, open **Route tables**.
2. For the **public subnets**’ route table:
   - There should be:
     - Destination: `0.0.0.0/0` → Target: Internet Gateway (`igw-xxxx`).
3. For the **private subnets**:
   - There should be:
     - Destination: `0.0.0.0/0` → Target: NAT Gateway (`nat-xxxx`).

This ensures:

- Public subnets can receive direct internet traffic.
- Private subnets have outbound internet access (via NAT) but no inbound from the internet.

---

### 2.4 Create security groups

In the **EC2 → Security Groups** section, create three SGs.

#### 2.4.1 ALB security group (`sg-alb`)

- **Name**: `prod-llm-alb-sg`.
- **VPC**: select your `prod-llm-vpc`.

Inbound rules:

- Rule 1 (HTTP, non‑TLS to start):
  - Type: `HTTP`.
  - Port: `80`.
  - Source: `0.0.0.0/0` (internet) for now.

You can add HTTPS later with ACM and TLS; for now we focus on structure.

Outbound rules:

- Allow all outbound (default), or restrict later.  
  The important flow is: ALB → EC2 on app port.

#### 2.4.2 App security group (`sg-app`)

- **Name**: `prod-llm-app-sg`.
- **VPC**: `prod-llm-vpc`.

Inbound rules:

- Rule 1 – HTTP traffic from ALB only:
  - Type: `HTTP`.
  - Port: your app port (e.g. `80` or `8501` depending on how you expose it on EC2).
  - Source: **`prod-llm-alb-sg`** (reference the ALB SG, not `0.0.0.0/0`).

Outbound rules:

- Allow all outbound initially; later you can tighten to:
  - RDS SG on port 5432.
  - AWS service endpoints (SSM, Bedrock, etc.).

#### 2.4.3 DB security group (`sg-db`)

- **Name**: `prod-llm-db-sg`.
- **VPC**: `prod-llm-vpc`.

Inbound rules:

- Rule 1 – Postgres from app SG only:
  - Type: `PostgreSQL`.
  - Port: `5432`.
  - Source: `prod-llm-app-sg`.

Outbound:

- Leave default (all) or restrict as required.

Result:

- Internet → ALB (public subnet, `sg-alb`) → EC2 instances (private app subnets, `sg-app`) → RDS (private DB subnets, `sg-db`).

---

### 2.5 Optional: Bastion host or SSM Session Manager

For true production practice, you should **avoid direct SSH from the internet** to your app instances.

Options:

- **Option A – SSM Session Manager (recommended)**
  - Give your EC2 instances an IAM role with SSM permissions.
  - Use the SSM Agent + Session Manager to open a shell from the console without SSH.
  - No SSH port needs to be open in security groups.

- **Option B – Bastion host**
  - Create a small EC2 instance in a **public subnet**.
  - Open SSH to that bastion only from your IP.
  - From bastion, SSH into app instances in private subnets.

For DevOps skills, it’s good to at least understand both, and practice SSM Session Manager where possible.

---

### 2.6 Networking checklist before moving on

Before you configure IAM, ASGs, and ALB, confirm these points:

1. **VPC created** with CIDR `10.0.0.0/16` (or your choice).
2. **Public subnets** in two AZs with routes to IGW.
3. **Private app and DB subnets** in two AZs with routes to NAT (for app) and proper routing for DB.
4. **Security groups**:
   - `prod-llm-alb-sg` – HTTP 80 from `0.0.0.0/0`.
   - `prod-llm-app-sg` – app port from `prod-llm-alb-sg`.
   - `prod-llm-db-sg` – 5432 from `prod-llm-app-sg`.
5. (Optional but recommended): Plan to use SSM Session Manager rather than SSH directly.

Once this is in place, you have a good **network foundation** to place:

- ALB in public subnets.
- EC2 instances in app private subnets.
- RDS in DB private subnets.

Next: go to `03_iam_and_secrets_management.md` to define IAM roles and secrets strategy.

