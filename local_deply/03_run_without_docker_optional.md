### 3. Run locally without Docker (optional)

> This section is **optional**. Use it only if you specifically want to see how to run the app with plain Python on your machine. For most cases, **Docker Compose is easier and more consistent**.

We will:

1. Set up a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run Postgres (either via Docker or a local installation).
4. Run the backend and frontend directly with Python commands.

The exact commands may vary slightly depending on your OS, but the overall ideas are the same.

---

### 3.1 Prerequisites

You need:

- **Python 3.10+** installed (matching what the project expects).
- **pip** (Python package installer).
- Some way to run **Postgres**:
  - Either as a container using Docker, or
  - As a local Postgres installation on your OS.
- AWS credentials configured on your machine (same as for Docker path).

We’ll assume your project directory is:

```bash
/home/Akshay/AWS/EKS
```

---

### 3.2 Create and activate a virtual environment

From a terminal:

```bash
cd /home/Akshay/AWS/EKS

python3 -m venv venv
```

Activate it:

- On Linux/macOS:

  ```bash
  source venv/bin/activate
  ```

- On Windows (PowerShell):

  ```powershell
  venv\Scripts\Activate.ps1
  ```

When the venv is active, your prompt will usually show `(venv)` at the start.

---

### 3.3 Install Python dependencies

With the venv active:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs everything needed for:

- Backend (Flask, Bedrock client libs, database drivers, etc.).
- Frontend (Streamlit).

---

### 3.4 Start Postgres

You have two approaches here:

- **Option A – Postgres in Docker container** (recommended even in “non‑Docker” mode, because it isolates DB nicely).
- **Option B – Local Postgres installation** (for those who already have it set up).

#### 3.4.1 Option A – Postgres via Docker only

Even if you don’t use Docker for the whole app, you can still use Docker just for the database.

Run:

```bash
docker run --name local-llm-postgres \
  -e POSTGRES_USER=llm_user \
  -e POSTGRES_PASSWORD=llm_password \
  -e POSTGRES_DB=llm_db \
  -p 5432:5432 \
  -d postgres:16
```

This starts a Postgres server listening on `localhost:5432` on your machine.

Make sure your backend’s database connection settings match these values (user, password, DB name, host, port). If they are managed via environment variables, set them in your shell before starting the backend:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=llm_user
export DB_PASSWORD=llm_password
export DB_NAME=llm_db
```

> Adjust variable names to whatever your backend actually expects.

#### 3.4.2 Option B – Fully local Postgres (no Docker)

If you already have Postgres installed locally, you can:

- Create a new database and user for this app.
- Ensure it listens on `localhost:5432`.
- Point the backend’s DB configuration at it (same way as above, via environment variables or config).

The exact steps depend on your OS and existing Postgres setup, so they are not detailed here.

---

### 3.5 Set environment variables for backend and Bedrock

Your backend needs two types of configuration:

1. **Database connection** (covered above).
2. **AWS region and maybe model ID for Bedrock**.

For example (adjust names to match your backend code):

```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=your-bedrock-model-id
```

Make sure your AWS credentials (from `aws configure` or other method) have permission to invoke Bedrock in that region.

---

### 3.6 Run the backend directly

With venv active and env vars set, from the project root:

```bash
cd /home/Akshay/AWS/EKS/backend

python app.py
```

or, if the backend uses a specific entrypoint (e.g. `flask run`, `uvicorn`, etc.), follow that convention, for example:

```bash
flask run --host 0.0.0.0 --port 8000
```

Check the backend logs for:

- Server starting successfully on some port (e.g. 8000).
- No fatal errors about database or Bedrock.

Make a note of the listening port (e.g. `http://localhost:8000`).

---

### 3.7 Run the frontend (Streamlit) directly

Open a **second terminal**, activate the same venv, and run:

```bash
cd /home/Akshay/AWS/EKS

source venv/bin/activate  # or appropriate command on your OS

cd frontend
streamlit run app.py --server.port 8501
```

If your frontend needs to know where the backend is listening, you might:

- Set an environment variable like:

  ```bash
  export BACKEND_URL=http://localhost:8000
  ```

- Or adjust a configuration file, depending on how the frontend is coded.

Streamlit will start and show a URL in the terminal, usually `http://localhost:8501`.

---

### 3.8 Open the app in your browser

Now open:

```text
http://localhost:8501
```

You should see the Streamlit UI.

Interaction will work like:

- Streamlit sends requests to the backend at `http://localhost:8000` (or whatever port you used).
- Backend talks to Postgres and Bedrock.
- Responses go back to Streamlit for display.

If something breaks:

- Check:
  - Backend terminal logs.
  - Frontend terminal logs.
  - Postgres container or service logs (if using Docker).

---

### 3.9 Stopping everything (non‑Docker path)

- **Frontend**: stop the Streamlit process with `Ctrl + C` in its terminal.
- **Backend**: stop the Python server with `Ctrl + C` in its terminal.
- **Postgres** (if using Docker):

  ```bash
  docker stop local-llm-postgres
  docker rm local-llm-postgres   # optional, removes the container
  ```

- Deactivate the venv when you’re done:

  ```bash
  deactivate
  ```

---

### 3.10 Summary – non‑Docker local path

You have seen how to:

- Use a Python virtual environment for dependencies.
- Run Postgres via a standalone container or local installation.
- Start backend and frontend as normal Python processes.

This gives you a deeper understanding of **what the containers are doing for you** in the Docker path. For day‑to‑day work, you can choose:

- **Docker Compose** for convenience and consistency, or
- **Direct Python** when you want tight control and debugging inside your IDE.

