### Local deployment – overview

This folder explains **how to run this Bedrock LLM demo app on your own laptop**, in the simplest and most repeatable way.

You already have some instructions in the root `README.md` (quick `docker compose` usage). Here we go **slower and more step‑by‑step**, assuming you are new.

We cover **two main ways** to run the app locally:

- **Recommended: Docker Compose** (everything in containers – Postgres, backend, frontend).
- **Optional: Direct Python** (using `venv` on your machine, Postgres via Docker or installed locally).

You do **not** have to do both. If you are happy with containers, just follow the Docker path.

---

### Files in this folder

- `01_local_concepts.md` – what “local deployment” means, Docker vs non‑Docker, ports, environment variables, and how Bedrock is reached from your laptop.
- `02_run_with_docker_compose.md` – very detailed steps to install Docker/Docker Compose (if needed) and run the whole stack locally with one command.
- `03_run_without_docker_optional.md` – optional: how to run backend and frontend directly with Python virtual environments and a Postgres database.

Follow them **in order** for the smoothest experience.

