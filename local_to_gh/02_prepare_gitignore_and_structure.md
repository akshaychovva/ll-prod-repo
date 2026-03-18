# 2. Prepare .gitignore and project structure

Before pushing, ensure `.gitignore` is correct so you never accidentally commit secrets or junk.

---

## 2.1 Your current .gitignore

You already have:

```
.env
venv/
```

That’s good, but we should add more entries for safety.

---

## 2.2 Recommended .gitignore (add these)

Add these lines to your `.gitignore` (at the project root, `/home/Akshay/AWS/EKS/.gitignore`):

```
# Already there
.env
venv/

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Secrets and keys (CRITICAL)
*.pem
*.key
.ssh/
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker (optional – usually you want to push Dockerfiles)
# Uncomment only if you have local override files you don't want to share
# docker-compose.override.yml
```

**Why each matters:**

- `*.pem`, `*.key`, `.ssh/` – prevents committing SSH or TLS keys.
- `__pycache__/`, `*.pyc` – Python bytecode, not source.
- `.env.local`, `.env.*.local` – local overrides that might contain secrets.

---

## 2.3 Optional: .env.example (document what env vars are needed)

Create a file `.env.example` that **documents** which environment variables your app needs, **without** real values:

```bash
# .env.example – copy to .env and fill in real values
# Never commit .env – it contains secrets

AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# DB (used by docker-compose; defaults are in docker-compose.yml)
# POSTGRES_DB=llm_app
# POSTGRES_USER=llm_user
# POSTGRES_PASSWORD=your-secret-password
```

Then add to your README:

```text
Copy .env.example to .env and fill in your values. Do not commit .env.
```

This helps others (and future you) know what to configure.

---

## 2.4 Project structure (what you have – good for Docker Compose)

Your layout is appropriate for Docker Compose:

```
EKS/
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── bedrock_client.py
│   └── Dockerfile
├── frontend/
│   ├── app.py
│   └── Dockerfile
├── docker-compose.yml      # Runs db, backend, frontend
├── requirements.txt        # Shared by both Dockerfiles
├── k8s/                    # For EKS later
├── docs/
├── ec2_deply/
├── ec2_deploy_steps/
├── ci_cd_deploy/
├── local_deply/
├── local_to_gh/
├── README.md
└── .gitignore
```

**No changes needed** – this structure works well. `docker-compose.yml` uses `context: .` and `dockerfile: backend/Dockerfile` / `frontend/Dockerfile`, which is correct.

---

## 2.5 Quick check before pushing

Run this from your project root:

```bash
cd /home/Akshay/AWS/EKS

# See what Git would add (dry run)
git status
git add -n .
```

Look at the list. If you see:

- `.env`
- `venv/`
- `*.pem`
- `.ssh/`

then `.gitignore` is not working. Fix it before committing.

---

## 2.6 Summary

- Update `.gitignore` with the recommended entries.
- Optionally add `.env.example` to document required env vars.
- Your project structure is fine for Docker Compose.

Next: `03_create_github_repo.md` to create the GitHub repository.
