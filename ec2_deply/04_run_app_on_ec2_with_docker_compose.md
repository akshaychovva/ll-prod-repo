### 4. Run the app on EC2 using Docker Compose

By now, you should have:

- An EC2 instance running (Amazon Linux 2023 or similar).
- Docker and Docker Compose installed.
- This project present on the instance (e.g. `/home/ec2-user/AWS/EKS`).

In this document, we will:

1. Confirm environment variables / AWS credentials behavior.
2. Build and run the containers on EC2 with `docker compose`.
3. Open the Streamlit UI from your browser using the EC2 public IP.
4. Optional: run in detached mode and check logs.

---

### 4.1 Change into the project directory

SSH into the EC2 instance if you’re not already in:

```bash
ssh -i ~/.ssh/bedrock-ec2-key.pem ec2-user@<EC2_PUBLIC_IP>
```

Then:

```bash
cd /home/ec2-user/AWS/EKS
pwd
```

You should see something like:

```bash
/home/ec2-user/AWS/EKS
```

List files:

```bash
ls
```

You should see at least:

- `docker-compose.yml`
- `backend/`
- `frontend/`
- `k8s/`
- `docs/`
- `ec2_deply/`

---

### 4.2 How AWS credentials work inside the containers on EC2

Your **backend** will call **AWS Bedrock**.

There are two common patterns:

1. **Use the EC2 instance IAM role (recommended)**:
   - The instance has an IAM role attached (from `02_create_ec2_instance.md`).
   - The containers inherit the ability to call Bedrock using the metadata service and the default credential provider chain.
   - You **do not set explicit AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY** in environment variables.

2. **Use explicit AWS credentials (not recommended for production)**:
   - You set environment variables or a mounted credentials file.
   - More manual work and more risk if you’re not careful.

For this learning/demo setup, we assume pattern **(1)**:

- You attached an IAM role with Bedrock permissions to the EC2 instance.
- Your existing backend code should work as long as it uses the normal AWS SDK defaults (no hardcoded keys).

If later you discover Bedrock calls fail with `AccessDenied`, you can:

- Check the IAM role policy.
- Check that the role is attached to this instance.
- Temporarily add more permissive Bedrock actions to confirm.

---

### 4.3 Build and start containers (foreground mode first)

From `/home/ec2-user/AWS/EKS`, run:

```bash
docker compose up --build
```

What this does:

- **Builds images** for:
  - `backend` (from `backend/Dockerfile`)
  - `frontend` (from `frontend/Dockerfile`)
- **Starts containers** for:
  - Postgres database
  - Backend API
  - Streamlit frontend

This is the **same command** you ran on your local machine (see the root `README.md`).

The first time, build might take a while (depending on image and network).

Watch for:

- Backend starting without fatal errors (look for log lines mentioning Flask, Uvicorn, or similar).
- Streamlit starting and listening on port 8501.

Leave this running for a moment and **do not close the SSH session** yet.

---

### 4.4 Open the Streamlit UI from your browser

On your **local machine**, open a browser and go to:

```text
http://<EC2_PUBLIC_IP>:8501
```

Replace `<EC2_PUBLIC_IP>` with the public IPv4 address from the EC2 console.

If your security group is correct (port 8501 open from your IP), you should see the same Streamlit UI that you saw locally.

If it doesn’t work:

- Check security group:
  - In the EC2 console, open your instance → Network → Security groups.
  - Confirm there is an inbound rule:
    - Type: Custom TCP (or All TCP)
    - Port range: 8501
    - Source: your IP (or 0.0.0.0/0 for testing only).
- Check that Docker is running and containers are up:

  ```bash
  docker ps
  ```

  You should see containers for Postgres, backend, and frontend.

---

### 4.5 Run in detached mode (background) for long‑running use

Running `docker compose up` in the foreground ties up your SSH session.

To run in the background:

1. First stop the current run:

   - In the SSH window where `docker compose up` is running, press `Ctrl + C`.

2. Start in **detached mode**:

   ```bash
   docker compose up --build -d
   ```

   The `-d` flag means **detached**.

3. Confirm that containers are running:

   ```bash
   docker ps
   ```

   You should see all services with `STATUS` like `Up ...`.

4. Now you can **disconnect SSH** and the containers will continue running.

You can always reconnect later and check:

```bash
ssh -i ~/.ssh/bedrock-ec2-key.pem ec2-user@<EC2_PUBLIC_IP>

cd /home/ec2-user/AWS/EKS
docker ps
```

---

### 4.6 Checking logs and debugging on EC2

To see logs for a specific service, use:

```bash
cd /home/ec2-user/AWS/EKS

docker compose logs -f backend
```

or

```bash
docker compose logs -f frontend
docker compose logs -f db   # if your postgres service is named "db"
```

The `-f` flag follows the logs (like `tail -f`).

To see logs from all services:

```bash
docker compose logs -f
```

Common things to check:

- Backend can reach Bedrock:
  - If there’s an IAM or permissions issue, logs will show errors from AWS SDK.
- Database is running and reachable:
  - Look for connection errors if backend cannot talk to Postgres.

---

### 4.7 Stopping the app

To **stop** all the containers started by this `docker-compose.yml`:

```bash
cd /home/ec2-user/AWS/EKS
docker compose down
```

This stops and removes containers (but not the images).

If you only want to stop services temporarily without destroying volumes, `down` is still fine for dev. For more advanced setups, you can adjust flags to keep volumes.

---

### 4.8 Summary – what you achieved

At this point, you have:

- A **single EC2 instance** in your chosen region.
- Docker and Docker Compose installed.
- This app running inside containers on that instance.
- Streamlit UI accessible at `http://<EC2_PUBLIC_IP>:8501`.

This is the **minimal cloud deployment** of your app using **EC2 only**, without Kubernetes.

For ideas on making this more robust and closer to production (backups, HTTPS, domain name, etc.), see `05_hardening_and_next_steps.md`.

