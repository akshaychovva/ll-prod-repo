### EC2 deployment – overview

This folder explains how to deploy **this Bedrock LLM demo app** on a **single EC2 instance**, which is the simplest way to get it running in the cloud before moving to Kubernetes/EKS.

The idea is:

- **You already know the app locally** (Docker + Docker Compose).
- **EC2 is “a Linux server in AWS”**.
- We will:
  - **Create an EC2 instance**.
  - **Install Docker + Docker Compose** on it.
  - **Copy this project** to the instance (or clone from Git).
  - **Run the same `docker compose up`** you used on your laptop.
  - Access Streamlit via the EC2 **public IP + port 8501**.

You do **not** change any application code. You are only changing **where** the containers run (your laptop → EC2).

---

### Files in this folder

- `01_concepts_ec2_vs_eks.md` – what EC2 is, how it compares to EKS, what pieces we need (network, IAM, security groups, key pairs).
- `02_create_ec2_instance.md` – step‑by‑step guide to create the EC2 instance in the AWS Console.
- `03_install_docker_and_clone_repo.md` – how to SSH into the instance, install Docker + Docker Compose, and get this project onto the instance.
- `04_run_app_on_ec2_with_docker_compose.md` – how to start the app with Docker Compose, expose ports, and test it.
- `05_hardening_and_next_steps.md` – optional: improving security, persistence, and turning this into something closer to production.

If you follow these files **in order**, you will have the app running on a single EC2 instance.

