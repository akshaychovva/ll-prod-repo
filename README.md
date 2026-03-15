## Bedrock LLM Demo – Streamlit + Flask + Postgres (Docker + EKS)

This project is a **very small, realistic full-stack app**:

- **Frontend**: `Streamlit` web UI
- **Backend**: `Flask` API
- **Database**: `Postgres`
- **AI**: calls an LLM in **AWS Bedrock**
- **Local run**: with **Docker Compose**
- **Cloud run**: with **Kubernetes manifests** ready for **AWS EKS**

You said: *“consider me very new”* — so the documentation is written step‑by‑step and explains each file and the important lines.

For detailed explanations, see the `docs/` folder:

- `docs/01_overview.md` – big picture + request flow
- `docs/02_backend.md` – Flask, Postgres, Bedrock line‑by‑line
- `docs/03_frontend.md` – Streamlit app line‑by‑line
- `docs/04_docker_and_k8s.md` – Docker, Kubernetes, EKS, secrets, edge cases

### Quick start – run everything locally with Docker

Prerequisites:

- Docker installed
- Docker Compose installed
- AWS credentials on your machine that can call Bedrock

Steps:

```bash
cd /home/Akshay/AWS/EKS

# 1) Build and start all services
docker compose up --build

# 2) Open the browser
#    Streamlit UI: http://localhost:8501
```

What happens:

- `docker-compose.yml` starts **Postgres**, **Flask backend**, **Streamlit frontend**
- Frontend sends your prompt to backend
- Backend calls **Bedrock**, stores the request/response into Postgres, and returns the text

### Very high‑level EKS steps (details in docs/04_docker_and_k8s.md)

1. **Build & push images** to a registry (e.g. Amazon ECR).
2. **Create an EKS cluster** (e.g. with `eksctl`).
3. **Create ConfigMap + Secret** for Postgres and Bedrock settings.
4. **Apply manifests**:
   - `k8s/config-and-secrets.yaml`
   - `k8s/postgres-statefulset.yaml`
   - `k8s/backend-deployment.yaml`
   - `k8s/frontend-deployment.yaml`
5. Get the **LoadBalancer URL** from `llm-frontend` service; open it in a browser.

For full line‑by‑line explanations and AWS/EKS/secret management details, open the files in `docs/` and follow them in order.

