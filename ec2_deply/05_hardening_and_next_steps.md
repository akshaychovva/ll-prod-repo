### 5. Hardening and next steps (optional, more advanced)

You now have a **minimal EC2 deployment**:

- One EC2 instance.
- Docker + Docker Compose.
- App accessible via `http://<EC2_PUBLIC_IP>:8501`.

This is perfect for learning and small demos. This document briefly explains how you might **improve** it over time and how it connects to **EKS**.

You do not need to implement everything here right now – treat this as a **map for future improvements**.

---

### 5.1 Security group tightening

Right now, you probably:

- Allow **SSH (22)** from your IP.
- Allow **Streamlit (8501)** from your IP (or from anywhere if you chose `0.0.0.0/0`).

Improvements:

- **Restrict sources**:
  - Use **“My IP”** instead of `0.0.0.0/0` for 8501, if this is just for you.
- **Change ports**:
  - Optionally run a reverse proxy (e.g. Nginx) and expose:
    - Port `80` (HTTP) and maybe `443` (HTTPS) instead of 8501.
  - This allows more standard URLs.

Changes are done in the **security group** attached to the instance.

---

### 5.2 Using a domain name and HTTPS

Right now you access:

```text
http://<EC2_PUBLIC_IP>:8501
```

To make it more user‑friendly and secure:

1. **Domain name**:
   - Register a domain (e.g. in Route 53 or any registrar).
   - Create a **DNS A record** pointing `app.yourdomain.com` to the EC2 public IP.

2. **HTTPS with a reverse proxy**:
   - Run **Nginx** or **Caddy** as another container (or installed on host).
   - Use **Let’s Encrypt** to obtain a free TLS certificate.
   - Terminate HTTPS at Nginx, then proxy to the Streamlit container on port 8501.

This is a bigger step, but very valuable if you ever expose the app to real users.

---

### 5.3 Data persistence and backups

Currently, your Postgres container likely uses a **Docker volume** for storage.

Improvements:

- Mount the database volume to a specific host path with regular backups.
- Snapshot the **EBS volume** attached to your EC2 instance periodically.
- For more serious setups:
  - Use a managed database like **Amazon RDS** for Postgres instead of a container.

The main idea:

- Don’t rely on a single disk with no backup if the data is important.

---

### 5.4 Observability (logs and metrics)

For learning, `docker compose logs` is enough.

For something more robust:

- **Logs**:
  - Ship logs to **CloudWatch Logs** using:
    - AWS CloudWatch agent on the host, or
    - Logging drivers that send container logs to CloudWatch.
- **Metrics**:
  - Use CloudWatch metrics for EC2 CPU/RAM/disk.
  - Or add Prometheus/Grafana in the future (especially when moving to Kubernetes).

This helps you:

- Detect issues early.
- Understand load and usage patterns.

---

### 5.5 Automating deployment

Right now, deployment steps are **manual**:

- SSH in
- `git pull` or `scp`
- `docker compose up --build -d`

Next steps could be:

- Shell script on EC2 that:
  - Pulls the latest code
  - Builds images
  - Restarts containers
- A simple **CI/CD pipeline**:
  - GitHub Actions / GitLab CI / CodePipeline.
  - On push to `main`, build images and:
    - Either push to a registry and pull from EC2.
    - Or deploy to a more automated environment like ECS/EKS.

Automation reduces human error and makes updates safer.

---

### 5.6 Connecting this to EKS later

Your current journey:

1. **Local Docker Compose** – understand the app.
2. **Single EC2 + Docker Compose** – understand running in the cloud on one machine.
3. **EKS (Kubernetes)** – understand running on many machines with orchestration.

How this EC2 setup helps you understand EKS:

- **Concepts you already saw**:
  - EC2 instances (EKS worker nodes are EC2 under the hood).
  - Security groups and ports.
  - IAM roles for Bedrock.
  - Docker images and containers.

- When you move to EKS:
  - Instead of running `docker compose up` on one instance, you:
    - Push images to a registry (ECR).
    - Create Kubernetes **Deployments** and **Services**.
    - Let EKS schedule containers on a **cluster** of EC2 instances.
  - The manifests in the existing `k8s/` folder are designed for that.

So this EC2 deployment is a **stepping stone**: you know your app works in the cloud, you understand networking and IAM basics, and you’re ready to take on Kubernetes concepts next.

---

### 5.7 When to stop the EC2 instance

Don’t forget that EC2 costs money while running.

- For saving money:
  - Stop the instance when you’re not using it.
  - Or terminate if you don’t need it anymore (but that deletes the data on the instance unless you’ve backed it up).

From the EC2 console:

- Select the instance → **Instance state** → **Stop**.

Later you can:

- Start it again and re‑use the setup (containers and volumes will still be there).

---

### 5.8 Summary

You now have:

- A **minimal but real** cloud deployment on EC2.
- A clear picture of:
  - Security groups and ports.
  - IAM role usage for Bedrock.
  - Docker + Docker Compose on a remote Linux server.
  - Where to go next for robustness (HTTPS, backups, observability, automation).

This gives you the confidence that your app is not only running locally and on Kubernetes, but can also run on a **very small, simple cloud footprint: one EC2 instance**.

