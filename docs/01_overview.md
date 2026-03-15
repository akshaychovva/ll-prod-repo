## 01 – Overview: what this app does

Read this file **first**. It explains the big picture without going too deep into code.

### What you are building

- **Streamlit frontend** – a simple web UI where you type a prompt.
- **Flask backend** – exposes:
  - `GET /health` – health check (for you + Kubernetes).
  - `POST /llm` – accepts a `prompt`, calls **AWS Bedrock**, returns model output.
- **Postgres database** – stores each prompt + response (for simple logging).
- **AWS Bedrock** – actually runs the LLM (Claude 3 Haiku by default).
- **Docker** – packages each piece into containers.
- **Kubernetes/EKS** – runs those containers on AWS.

### High‑level request flow

1. You open the **Streamlit UI** in your browser.
2. You type a prompt and click **“Send to LLM”**.
3. The Streamlit app sends an HTTP `POST` to the Flask backend:
   - URL: `BACKEND_URL/llm`
   - Body: `{"prompt": "your text here"}`.
4. The Flask backend:
   - Validates the JSON (`prompt` must not be empty).
   - Calls **AWS Bedrock** using the **boto3** SDK.
   - Gets the text back from the LLM.
   - Stores prompt + response in **Postgres**.
   - Returns the response as JSON to the frontend.
5. Streamlit displays the model’s answer on the page.

### Files and folders

- `requirements.txt` – Python dependencies for **both** frontend and backend.
- `backend/`
  - `app.py` – main Flask application, routes, health check, LLM endpoint.
  - `db.py` – connects to Postgres, creates a table, saves logs.
  - `bedrock_client.py` – wraps the AWS Bedrock API call.
  - `Dockerfile` – builds the backend container image.
- `frontend/`
  - `app.py` – Streamlit UI that calls the backend.
  - `Dockerfile` – builds the frontend container image.
- `docker-compose.yml` – runs **Postgres + backend + frontend** locally.
- `k8s/`
  - `backend-deployment.yaml` – backend Deployment + Service.
  - `frontend-deployment.yaml` – frontend Deployment + LoadBalancer Service.
  - `postgres-statefulset.yaml` – Postgres StatefulSet + Service.
  - `config-and-secrets.yaml` – ConfigMap + Secret (for DB + Bedrock).
- `docs/`
  - `01_overview.md` – this file.
  - `02_backend.md` – backend code explained line‑by‑line.
  - `03_frontend.md` – frontend code explained line‑by‑line.
  - `04_docker_and_k8s.md` – Docker, Kubernetes, EKS, secrets, edge cases.

### Local vs EKS mental model

- **Locally with Docker Compose**
  - One machine: your laptop.
  - Docker runs three containers: Postgres, backend, frontend.
  - Networking is simple:
    - Frontend talks to `backend:5000`.
    - Backend talks to `db:5432`.

- **On AWS EKS**
  - A cluster of EC2 instances or Fargate (managed by Kubernetes).
  - Each part (frontend/backend/db) is a **Pod** managed by a **Deployment/StatefulSet**.
  - Networking:
    - Pods talk to each other via Kubernetes **Services**.
    - The frontend has a `LoadBalancer` service, which gives you a public URL.

Once you are comfortable with this overview, open `docs/02_backend.md` to dive into the backend code line by line.

