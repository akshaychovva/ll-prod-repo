### 2. Run the app locally with Docker Compose (recommended)

This is the **simplest and most realistic** way to run the app on your laptop, because it matches how you will run it on EC2 and EKS.

We will:

1. Check/install Docker and Docker Compose.
2. Confirm your AWS credentials can call Bedrock.
3. Run `docker compose up --build`.
4. Open the app in the browser at `http://localhost:8501`.

---

### 2.1 Prerequisites

You need:

- A machine with:
  - Linux, macOS, or Windows.
  - Enough RAM (at least 4 GB total; more is better).
- **Docker** installed:
  - On Linux: Docker Engine + Docker Compose plugin.
  - On macOS/Windows: Docker Desktop.
- **AWS credentials** configured (same ones you use for other AWS work).

This project lives on your machine at (example):

```bash
/home/Akshay/AWS/EKS
```

Adjust if your path is different.

---

### 2.2 Check if Docker is installed

In a terminal on your machine, run:

```bash
docker --version
```

You should see something like `Docker version 24.x...`.

Next, check Docker Compose:

```bash
docker compose version
```

You should see `Docker Compose version v2.x...`.

- If Docker is missing:
  - Install it from the official docs for your OS.
- If only Compose is missing:
  - On modern Docker, Compose is a plugin (`docker compose` with a space).
  - On older systems you might have the old `docker-compose` binary instead.

As long as you have **some working Docker + Compose** setup, you’re fine.

---

### 2.3 Check AWS credentials locally

Make sure your AWS CLI works and has permissions for Bedrock in the target region.

Run:

```bash
aws sts get-caller-identity
```

If you see an error like “Unable to locate credentials”, run:

```bash
aws configure
```

and provide:

- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g. `us-east-1`)
- Default output format (`json` is fine)

Then verify again:

```bash
aws sts get-caller-identity
```

If this works, your Bedrock calls from the backend are more likely to work too (assuming IAM permissions are correct).

---

### 2.4 Change into the project directory

In your terminal:

```bash
cd /home/Akshay/AWS/EKS
pwd
```

You should see:

```bash
/home/Akshay/AWS/EKS
```

List files:

```bash
ls
```

You should see:

- `docker-compose.yml`
- `backend/`
- `frontend/`
- `k8s/`
- `docs/`
- `ec2_deply/`
- `local_deply/`
- and possibly `venv/`.

---

### 2.5 Build and start the stack

From the project root, run:

```bash
docker compose up --build
```

This does two main things:

1. **Build images** (if not already built or if changed):
   - `backend` image from `backend/Dockerfile`.
   - `frontend` image from `frontend/Dockerfile`.
2. **Start containers** as defined in `docker-compose.yml`:
   - Postgres database container.
   - Backend API container.
   - Streamlit frontend container (port 8501 exposed to localhost).

The first build may take a few minutes (downloads base images, installs dependencies).

While it runs:

- Watch the logs in the terminal.
- Look for:
  - Database initializing successfully.
  - Backend starting without fatal errors.
  - Streamlit starting and listening on port 8501.

If there are errors, the logs in this terminal are your first place to debug.

---

### 2.6 Open the app in your browser

Once the containers are up and stable, open a browser on your laptop and go to:

```text
http://localhost:8501
```

You should see the Streamlit UI.

From there:

- Enter a prompt.
- Submit it.
- Watch the backend talk to Bedrock and Postgres.

If the page does not load:

- Make sure `docker compose up` is still running (no crash).
- Check that port 8501 is indeed exposed in `docker-compose.yml`.
- Check Docker Desktop/Engine is actually running.

---

### 2.7 Running in detached mode (background)

By default, `docker compose up` runs in the **foreground**.

To run it in the background:

1. Stop the current foreground run with `Ctrl + C`.
2. Start in detached mode:

   ```bash
   docker compose up --build -d
   ```

3. List running containers:

   ```bash
   docker ps
   ```

   You should see containers for the database, backend, and frontend.

You can now close your terminal; the containers will keep running until you stop them.

---

### 2.8 Viewing logs while running detached

To see logs:

```bash
cd /home/Akshay/AWS/EKS

docker compose logs -f
```

Or for a specific service:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db      # or whatever your DB service is named
```

`-f` (“follow”) shows new log lines in real time.

This is useful to:

- Debug Bedrock errors.
- See database connection issues.
- Watch request/response flow.

---

### 2.9 Stopping the local stack

To stop containers started by this `docker-compose.yml`:

```bash
cd /home/Akshay/AWS/EKS
docker compose down
```

This:

- Stops all services.
- Removes containers (but not images or volumes, unless configured otherwise).

You can always start again with:

```bash
docker compose up --build
```

or

```bash
docker compose up --build -d
```

---

### 2.10 Summary – local Docker path

You have now:

- Used **Docker Compose** to run:
  - Postgres.
  - Flask backend.
  - Streamlit frontend.
- Accessed the app at `http://localhost:8501`.
- Learned how to:
  - Start (`up`), stop (`down`), and inspect (`logs`, `ps`) the stack.

This is the **recommended** way to work locally, especially since it mirrors EC2/EKS behavior.  
If you want to see the non‑Docker, direct Python approach (for learning), check `03_run_without_docker_optional.md`.

