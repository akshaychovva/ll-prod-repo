### 1. Concepts – EC2 vs EKS and what we will build

This document explains **what EC2 is**, how it compares to **EKS**, and what exact pieces we will create in AWS for this simple deployment.

You can read this once, slowly, and then follow the later step‑by‑step guides.

---

### 1.1 What is EC2 (very simple view)

Think of **EC2** as:

- **A virtual Linux machine in AWS**.
- It is similar to:
  - A Linux VM in VMware / VirtualBox.
  - A physical Linux server in a data center.
- On that Linux machine, you can:
  - Install packages (`yum`, `dnf`, `apt`, etc.).
  - Install Docker and run containers.
  - Copy files, run scripts, etc.

When you launch an **EC2 instance**, you choose:

- **AMI**: the OS image (e.g. Amazon Linux 2023, Ubuntu 22.04).
- **Instance type**: CPU/RAM size (e.g. `t3.small`, `t3.medium`).
- **Storage**: how many GB of disk (e.g. 20 GB gp3).
- **Network**:
  - VPC, subnet.
  - **Security group** – like a firewall (which inbound ports are open).
- **Key pair** – used for SSH login.
- **IAM role** – what AWS permissions the instance has (e.g. to call Bedrock).

In this project, we will:

- Use **one EC2 instance**.
- Install **Docker and Docker Compose**.
- Run **the same containers** you already run locally.

---

### 1.2 How this compares to EKS

You already have manifests for **EKS (Kubernetes)**:

- EKS = **many machines + an orchestrator** that schedules containers.
- EC2 (by itself) = **single machine you manage directly**.

High‑level differences:

- **EKS**
  - You define **Deployments**, **Services**, **StatefulSets**, etc.
  - Kubernetes decides **where containers run**, health checks, restarts, scaling.
  - Good for production, high availability, auto‑scaling.
  - More moving parts and more concepts to learn at once.

- **EC2 only**
  - You directly control **one Linux server**.
  - You manually start Docker containers (or Docker Compose).
  - No built‑in auto‑scaling or orchestration.
  - Very good for **learning**, dev/test, and simple demos.

For now, we intentionally **don’t use Kubernetes**. We just want:

- “Take my app that already runs in Docker on my laptop, and run the same thing in the cloud on a single EC2 machine.”

---

### 1.3 What components we need in AWS for this app

Your app has:

- **Frontend** – Streamlit container.
- **Backend** – Flask container.
- **Database** – Postgres container.
- **Bedrock** – external AWS service accessed via API.
ake my app that already runs in Docker on my laptop, and run the same thing in the cloud on a single EC
When running on **one EC2 instance**, we need:

- **EC2 instance** in a VPC + subnet.
- **Security group** that allows:
  - Inbound **SSH (port 22)** from your IP (for administration).
  - Inbound **port 8501** from your IP (for Streamlit UI).
    - Optional: Inbound **backend port** (if you access backend directly) – but usually Streamlit talks to backend internally.
- **IAM role** attached to EC2 that allows:
  - Calling **Bedrock InvokeModel** APIs (same region as your Bedrock model).
- **Key pair** for SSH:
  - You download a `.pem` file once.
  - You use it to SSH as `ec2-user` (Amazon Linux) or `ubuntu` (Ubuntu).

We do **not** need:

- Load balancers, Auto Scaling Groups, multiple AZs, etc. (for this first minimal setup).

---

### 1.4 Where Docker fits in

You already have:

- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`

Locally, you run:

```bash
docker compose up --build
```

That:

- Builds images for **backend** and **frontend**.
- Starts **Postgres**, **backend**, and **frontend** containers.

On **EC2**, we will do **exactly the same thing**:

1. Install Docker + Docker Compose.
2. Copy this whole project to EC2 (or `git clone` it).
3. Run `docker compose up --build -d` on the EC2 instance.

So you don’t need to learn new Docker concepts here – it’s the same usage, just a different machine.

---

### 1.5 How AWS credentials will work on EC2

Your backend calls **AWS Bedrock**. Locally, you probably used:

- `~/.aws/credentials` and environment variables, or
- some other default AWS config.

On EC2, the best practice for a simple setup is:

- Attach an **IAM role** to the EC2 instance when you create it.
- That IAM role has a policy like:
  - `bedrock:InvokeModel`
  - `bedrock:InvokeModelWithResponseStream`
  - Limited to the region and model(s) you actually use.
- Inside the EC2 instance, the **AWS SDK picks up the instance role automatically**.

So, inside your backend container you **do not need explicit AWS keys** in env vars if your containers use the default provider chain and can see the EC2 metadata service. (For simple demos this usually works fine. If not, you can still set explicit env vars; just remember not to commit secrets to Git.)

---

### 1.6 Big picture of what you will actually do

At a very high level, you will:

1. **Create EC2**
   - Choose region, AMI (Amazon Linux 2023 or Ubuntu), instance type (e.g. `t3.small` or `t3.medium`), disk size (e.g. 30 GB).
   - Create/choose:
     - Security group (open ports 22, 8501 from your IP).
     - Key pair (for SSH).
     - IAM role (with Bedrock permissions).

2. **Connect to EC2 via SSH**
   - Use the `.pem` key.
   - Confirm you can run `ls`, `uname -a`, etc.

3. **Install Docker and Docker Compose**
   - Using package manager and official Docker instructions for that OS.

4. **Copy the project to EC2**
   - Either:
     - Use `git clone` from your repository, or
     - Use `scp` / `rsync` to upload the local folder.

5. **Run Docker Compose**
   - `cd` into the project directory.
   - Run `docker compose up --build -d`.

6. **Test the app from your browser**
   - Use `http://<EC2_PUBLIC_IP>:8501`.

This is what the remaining markdown files in this `ec2_deply` folder will walk you through step by step.

