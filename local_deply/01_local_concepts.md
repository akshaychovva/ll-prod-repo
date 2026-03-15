### 1. Local deployment concepts

Before you type any commands, it helps to understand **what exactly is running on your laptop** and how the pieces talk to each other.

---

### 1.1 What “local deployment” means here

In this project, **local deployment** means:

- All parts of the app run on **your own machine**:
  - **Frontend** – Streamlit web app.
  - **Backend** – Flask API.
  - **Database** – Postgres.
- You open your browser at `http://localhost:<port>` to use it.

But even when running locally, the app still calls:

- **AWS Bedrock** – which is in AWS, not on your machine.

So for local deployment you need:

- A working **internet connection**.
- **AWS credentials** on your machine that can call Bedrock.

---

### 1.2 Two local options: Docker vs direct Python

You have two main ways to run the app locally:

- **Option A – Docker Compose (recommended)**
  - You install **Docker Desktop** (or Docker Engine + Docker Compose).
  - One command starts:
    - A Postgres container.
    - A backend (Flask) container.
    - A frontend (Streamlit) container.
  - Your host browser talks to the frontend on `http://localhost:8501`.
  - Very **repeatable** and **close to how it runs on EC2/EKS**.

- **Option B – Direct Python (optional)**
  - You install Python and Postgres on your host machine (or use Postgres in a Docker container).
  - You create a **virtual environment (venv)**.
  - You install dependencies with `pip install -r requirements.txt`.
  - You run backend and frontend via Python commands.
  - More “traditional” Python dev style, not container‑based.

For learning cloud/container concepts, **Option A (Docker Compose)** is strongly recommended. Option B is provided only if you want to see how things look without containers.

---

### 1.3 How services talk to each other locally (with Docker)

With Docker Compose:

- Docker creates a **virtual network** for the containers.
- Each service runs in its **own container** but can talk to others by:
  - **Service name** (e.g. `db`, `backend`, `frontend`).
  - Standard ports (Postgres 5432, HTTP ports for backend/frontend).

Typical flow:

1. You open `http://localhost:8501` in your browser.
2. Browser sends requests to the **frontend container**’s exposed port 8501.
3. Frontend sends requests internally (through Docker network) to the **backend container**.
4. Backend:
   - Reads/writes data in the **Postgres container**.
   - Calls **AWS Bedrock** using your AWS credentials.
5. Backend returns the result to frontend, which renders it for you.

From your point of view:

- You just see a web app at `http://localhost:8501`.
- All the container networking is hidden behind Docker Compose.

---

### 1.4 Ports and localhost

Even though the services are in containers, Docker maps certain **container ports** to your machine’s **localhost** ports.

Important points:

- You normally only need to care about the **frontend port**:
  - `http://localhost:8501` for Streamlit.
- Backend and database ports may or may not be exposed to your host, depending on the `docker-compose.yml` settings.
  - Even if they are not exposed, the **frontend can still reach the backend** over the Docker network.

So if you ever wonder “Why can Streamlit reach the backend, but my browser cannot call the backend port directly?” – it’s because:

- Docker is exposing the frontend port to your laptop,
- But keeping backend/internal ports only inside the Docker network (which is fine).

---

### 1.5 AWS credentials on your laptop

Your backend will call **AWS Bedrock** using an AWS SDK.

For local development, the SDK usually looks for credentials in the following places (in order):

1. **Environment variables**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN` (if using temporary credentials)
   - `AWS_REGION` or `AWS_DEFAULT_REGION`
2. **Shared credentials/config files**:
   - `~/.aws/credentials`
   - `~/.aws/config`
3. AWS SSO or other providers, depending on your setup.

When you run inside Docker:

- You can either:
  - Pass necessary env vars into the container, or
  - Mount `~/.aws` into the container, or
  - Use another method you have already configured in this project.

This repo’s existing Docker configuration is designed to work with whichever method you used previously when running locally with Docker Compose. If Bedrock calls fail, it’s usually due to **missing or incorrect AWS credentials or region**.

---

### 1.6 Summary – what you will actually do on your laptop

At a very high level, you will:

1. Ensure you have **Docker + Docker Compose** installed (or install them).
2. Ensure your **AWS credentials** are valid and configured (`aws configure` or env vars).
3. From the project root (e.g. `/home/Akshay/AWS/EKS`), run:

   ```bash
   docker compose up --build
   ```

4. Open:

   ```text
   http://localhost:8501
   ```

That’s it for the **Docker path**.

The next files in this folder expand those steps into a very detailed, line‑by‑line guide:

- `02_run_with_docker_compose.md` – full, step‑by‑step Docker path.
- `03_run_without_docker_optional.md` – optional bare‑metal Python path.

