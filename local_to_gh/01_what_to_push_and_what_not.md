# 1. What to push and what NOT to push

Before you push anything, you must understand **what belongs in Git** and **what must stay local**.

---

## 1.1 Why this matters

- **GitHub is public** (or shared) – anyone with access can see what you push.
- **Secrets in Git** = compromised forever (even if you delete them later, they stay in history).
- **Large or generated files** slow down clones and bloat the repo.

---

## 1.2 NEVER push these (security and hygiene)

| Item | Why |
|------|-----|
| `.env` | Contains secrets (DB passwords, API keys, etc.) |
| `venv/` | Python virtual environment – huge, machine-specific, reproducible from `requirements.txt` |
| `*.pem`, `*.key` | SSH keys, TLS keys – anyone with these can impersonate you |
| `~/.aws/` or any AWS credentials | Access keys – full account access |
| `__pycache__/`, `*.pyc` | Python bytecode – generated, not source |
| `.idea/`, `.vscode/` (optional) | IDE settings – often personal preference |
| `node_modules/` (if you add Node later) | Dependencies – reproducible from `package.json` |
| Docker volumes data | `pgdata/` etc. – runtime data, not code |

---

## 1.3 DO push these (your app and config)

| Item | Why |
|------|-----|
| `backend/` | Your Flask backend code |
| `frontend/` | Your Streamlit frontend code |
| `backend/Dockerfile` | How to build the backend image |
| `frontend/Dockerfile` | How to build the frontend image |
| `docker-compose.yml` | How to run the full stack locally |
| `requirements.txt` | Python dependencies (used by both Dockerfiles) |
| `k8s/` | Kubernetes manifests (for EKS later) |
| `docs/` | Project documentation |
| `ec2_deply/`, `ec2_deploy_steps/`, `ci_cd_deploy/`, `local_deply/`, `local_to_gh/` | Deployment guides |
| `README.md` | Project overview and quick start |
| `.gitignore` | Tells Git what to ignore |

---

## 1.4 How your Docker Compose setup fits

Your `docker-compose.yml`:

- Uses **build** for backend and frontend (builds from source in the repo).
- Uses **environment variables** for DB and Bedrock config.
- Mounts `~/.aws` for AWS credentials (stays on your machine, not in Git).

So:

- **Code and Dockerfiles** → push to GitHub.
- **Secrets and credentials** → stay local (`.env`, `~/.aws`).

Anyone who clones your repo can run:

```bash
docker compose up --build
```

They will need to:

- Have their own `.env` or set env vars for DB/Bedrock.
- Have AWS credentials configured (or use IAM role on EC2).

---

## 1.5 Summary

- **Push**: source code, Dockerfiles, docker-compose, docs, deploy guides.
- **Never push**: `.env`, `venv/`, `.pem`, AWS keys, `__pycache__`, IDE junk.

Next: `02_prepare_gitignore_and_structure.md` to make sure `.gitignore` is correct and your structure is ready.
