## 04 – Docker, Kubernetes, EKS, and secrets (with edge cases)

This is the “become a bro” section: we’ll go over

- Dockerfiles
- `docker-compose.yml`
- Kubernetes manifests for EKS
- Secret management
- Common edge cases and how to think about them

---

## Part 1 – Docker

### Backend Dockerfile – `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
```

- Base image: small Python 3.11 image (Debian slim).
- Trade‑off: smaller size vs needing to install some OS packages yourself if needed.

```dockerfile
WORKDIR /app
```

- Sets working directory **inside** the container to `/app`.
- All next commands run relative to this directory.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

- `PYTHONDONTWRITEBYTECODE=1` – don’t create `.pyc` files; reduces noise.
- `PYTHONUNBUFFERED=1` – makes Python output appear immediately (great for logs).

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

- Copy `requirements.txt` into the image.
- Install all Python dependencies.
- `--no-cache-dir` – don’t store pip cache, keeps image smaller.

```dockerfile
COPY backend/ .
```

- Copy your backend code into `/app` inside the image.

```dockerfile
ENV BACKEND_PORT=5000
EXPOSE 5000
```

- Set default `BACKEND_PORT`.
- `EXPOSE 5000` tells Docker/Kubernetes that this container listens on port `5000`.
  - Note: It does **not** actually publish the port on your host; that’s done by Docker Compose / k8s Services.

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

- Final command to run when container starts:
  - `gunicorn` – production‑ready WSGI server for Python.
  - `--bind 0.0.0.0:5000` – listen on all interfaces on port 5000.
  - `app:app` – module `app.py`, variable `app` (your Flask instance).

#### Backend Docker edge cases

- **Port mismatch**:
  - Container uses `5000`; if you map host port incorrectly (e.g. `8000:5000`), your app will be on `http://localhost:8000`, not `5000`.
  - Kubernetes uses `containerPort: 5000`; Service must target the same.
- **Missing dependencies**:
  - If you forget a library in `requirements.txt`, container will build, but app might crash at runtime with `ModuleNotFoundError`.
  - Fix: add dependency, rebuild image.

---

### Frontend Dockerfile – `frontend/Dockerfile`

Very similar to the backend one:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ .

ENV FRONTEND_PORT=8501
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Key differences:

- `FRONTEND_PORT=8501` and `EXPOSE 8501` – Streamlit default port.
- `CMD` uses `streamlit run app.py`.
- `--server.address=0.0.0.0` – allow connections from outside the container.

#### Frontend Docker edge cases

- **CORS / mixed origin**:
  - We keep it simple by letting frontend talk to backend within Docker/k8s network.
  - If you host Streamlit separately on the internet and backend elsewhere, you might need CORS configuration.

---

### Docker Compose – `docker-compose.yml`

This is for **local development**, not for EKS.

```yaml
version: "3.9"
```

- Compose file format version.

```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: llm-postgres
    environment:
      POSTGRES_DB: llm_app
      POSTGRES_USER: llm_user
      POSTGRES_PASSWORD: llm_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
```

- `db` service:
  - Uses official Postgres 15 Alpine image.
  - Sets database name, user, password via environment variables.
  - Exposes port `5432` to your host.
  - Uses a named volume `pgdata` so data survives container restarts.

```yaml
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: llm-backend
    environment:
      POSTGRES_HOST: db
      POSTGRES_PORT: 5432
      POSTGRES_DB: llm_app
      POSTGRES_USER: llm_user
      POSTGRES_PASSWORD: llm_password
      AWS_REGION: ${AWS_REGION:-us-east-1}
      BEDROCK_MODEL_ID: ${BEDROCK_MODEL_ID:-anthropic.claude-3-haiku-20240307-v1:0}
    ports:
      - "5000:5000"
    depends_on:
      - db
```

- `backend` service:
  - Built from `backend/Dockerfile`.
  - Connects to Postgres at host `db` (Docker internal DNS).
  - Reads AWS Bedrock settings from environment:
    - `AWS_REGION` – default `us-east-1`.
    - `BEDROCK_MODEL_ID` – default Claude 3 Haiku.
  - Exposes `5000` on host.
  - Waits for `db` to be created (`depends_on`), but **does not** guarantee DB is fully ready – we handled that in code via `init_db`.

```yaml
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    container_name: llm-frontend
    environment:
      BACKEND_URL: http://backend:5000
    ports:
      - "8501:8501"
    depends_on:
      - backend
```

- `frontend` service:
  - Built from `frontend/Dockerfile`.
  - `BACKEND_URL` points to `http://backend:5000` (Docker service name).
  - Exposes Streamlit on host port `8501`.

```yaml
volumes:
  pgdata:
```

- Defines the named volume used by Postgres.

#### Docker Compose edge cases

- **Order of startup**:
  - `depends_on` doesn’t wait until Postgres is ready; that’s why `init_db` is tolerant.
- **AWS credentials inside containers**:
  - Locally, you usually have `~/.aws/credentials` on your host.
  - If you run `docker compose up` without passing them, **boto3 inside the container will not see them** by default.
  - Simple option for local testing:
    - Mount `~/.aws` into the container **or**
    - Pass `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` explicitly as env vars (do not commit these to git).

---

## Part 2 – Kubernetes manifests (for EKS)

We assume:

- You have built and pushed images to a registry (e.g. Amazon ECR).
- You have an EKS cluster and `kubectl` configured to talk to it.

### ConfigMap and Secret – `k8s/config-and-secrets.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-config
data:
  AWS_REGION: "us-east-1"
  BEDROCK_MODEL_ID: "anthropic.claude-3-haiku-20240307-v1:0"
```

- `ConfigMap` holds **non‑secret** configuration:
  - Region and model ID.
- Easy to change without rebuilding images.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-secrets
type: Opaque
data:
  POSTGRES_DB: bGxtX2FwcA==
  POSTGRES_USER: bGxtX3VzZXI=
  POSTGRES_PASSWORD: bGxtX3Bhc3N3b3Jk
```

- `Secret` holds **sensitive** values (base64 encoded):
  - These are `llm_app`, `llm_user`, `llm_password` encoded in base64.
- To create your own:

```bash
echo -n "llm_app" | base64          # POSTGRES_DB
echo -n "llm_user" | base64         # POSTGRES_USER
echo -n "strongpassword" | base64   # POSTGRES_PASSWORD
```

> In real production you would **not** store DB passwords like this in git. Use:
> - External secret managers (AWS Secrets Manager, SSM Parameter Store) + CSI driver.
> - Or at least a private git repo, with restricted access.

---

### Postgres StatefulSet – `k8s/postgres-statefulset.yaml`

This runs Postgres **inside** the cluster (simpler demo). In production, consider AWS RDS instead.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-postgres
spec:
  clusterIP: None
  selector:
    app: llm-postgres
  ports:
    - name: postgres
      port: 5432
      targetPort: 5432
```

- Headless service for the StatefulSet (`clusterIP: None`).
- Name `llm-postgres` becomes the DNS name used by backend.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: llm-postgres
spec:
  serviceName: llm-postgres
  replicas: 1
  selector:
    matchLabels:
      app: llm-postgres
  template:
    metadata:
      labels:
        app: llm-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
```

- `StatefulSet` gives each pod a stable identity and persistent volume.
- Reads DB name/user/password from the `llm-secrets` Secret.
- Uses a `PersistentVolumeClaim` template to request 5Gi of storage.

#### Postgres in k8s edge cases

- **Data loss**:
  - If you delete the PVC, you lose the data.
  - That’s why many teams prefer using **RDS** instead of running Postgres in cluster.
- **Scaling**:
  - StatefulSet is set to `replicas: 1`. Scaling Postgres is non‑trivial (replication, failover).

---

### Backend Deployment + Service – `k8s/backend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-backend
  labels:
    app: llm-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-backend
```

- `Deployment` manages a set of identical pods (stateless).
- `replicas: 2` – two backend pods, for basic high availability.

```yaml
  template:
    metadata:
      labels:
        app: llm-backend
    spec:
      containers:
        - name: llm-backend
          image: your-dockerhub-username/llm-backend:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
```

- Pod template:
  - Container uses image `your-dockerhub-username/llm-backend:latest`.
    - Replace this with your actual image from ECR or Docker Hub.
  - Exposes port `5000` inside the pod.

```yaml
          env:
            - name: POSTGRES_HOST
              value: "llm-postgres"
            - name: POSTGRES_PORT
              value: "5432"
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: POSTGRES_PASSWORD
            - name: AWS_REGION
              valueFrom:
                configMapKeyRef:
                  name: llm-config
                  key: AWS_REGION
            - name: BEDROCK_MODEL_ID
              valueFrom:
                configMapKeyRef:
                  name: llm-config
                  key: BEDROCK_MODEL_ID
```

- Environment variables:
  - `POSTGRES_HOST` is `llm-postgres` Service.
  - DB name/user/password from Secret.
  - Bedrock region and model ID from ConfigMap.

```yaml
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 15
            periodSeconds: 20
```

- `readinessProbe`:
  - Checks `/health` to see if the app is ready to handle traffic.
  - Until it passes, the pod is **not** added to the Service endpoints.
- `livenessProbe`:
  - If it fails repeatedly, Kubernetes restarts the container.

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: llm-backend
spec:
  selector:
    app: llm-backend
  ports:
    - protocol: TCP
      port: 5000
      targetPort: 5000
  type: ClusterIP
```

- `Service` of type `ClusterIP`:
  - Exposes the backend on a stable DNS name: `llm-backend`.
  - Only accessible **inside** the cluster.
  - Frontend uses URL `http://llm-backend:5000`.

---

### Frontend Deployment + Service – `k8s/frontend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-frontend
  labels:
    app: llm-frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm-frontend
  template:
    metadata:
      labels:
        app: llm-frontend
    spec:
      containers:
        - name: llm-frontend
          image: your-dockerhub-username/llm-frontend:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8501
          env:
            - name: BACKEND_URL
              value: "http://llm-backend:5000"
```

- Single replica of the Streamlit frontend.
- `BACKEND_URL` points to the internal backend Service.

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: llm-frontend
spec:
  type: LoadBalancer
  selector:
    app: llm-frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8501
```

- `LoadBalancer` service:
  - EKS + your cloud provider create an external load balancer.
  - Users access the app via `http://EXTERNAL-IP/`.
  - Maps external port `80` to pod port `8501` (Streamlit).

#### Frontend in k8s edge cases

- **Waiting for LoadBalancer**:
  - After `kubectl apply`, it may take 1–10 minutes for an external IP to appear.
  - Use `kubectl get svc llm-frontend` and watch the `EXTERNAL-IP` column.

---

## Part 3 – AWS EKS: how to deploy

### Step 1 – Build and push images

Replace `your-dockerhub-username` below with your actual registry path. If you use ECR, the image name will be something like `123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-backend:latest`.

```bash
# From project root

# Build images
docker build -t llm-backend -f backend/Dockerfile .
docker build -t llm-frontend -f frontend/Dockerfile .

# Tag for your registry (Docker Hub example)
docker tag llm-backend your-dockerhub-username/llm-backend:latest
docker tag llm-frontend your-dockerhub-username/llm-frontend:latest

# Push
docker push your-dockerhub-username/llm-backend:latest
docker push your-dockerhub-username/llm-frontend:latest
```

Then update `image:` fields in:

- `k8s/backend-deployment.yaml`
- `k8s/frontend-deployment.yaml`

### Step 2 – Create an EKS cluster (high level)

There are many ways; one simple way is using `eksctl`:

```bash
eksctl create cluster \
  --name bedrock-demo \
  --region us-east-1 \
  --nodes 2
```

This may take 10–20 minutes. Once done, `kubectl` context will be configured.

### Step 3 – Apply ConfigMap and Secret

```bash
kubectl apply -f k8s/config-and-secrets.yaml
```

This creates:

- `ConfigMap/llm-config`
- `Secret/llm-secrets`

### Step 4 – Deploy Postgres, backend, frontend

```bash
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

Check status:

```bash
kubectl get pods
kubectl get svc
```

Once `llm-frontend` Service has an external IP:

- Open `http://EXTERNAL-IP/` in your browser.

---

## Part 4 – AWS credentials and secrets in EKS

### Recommended: IAM Role for Service Account (IRSA)

Instead of putting `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in a Secret (which is risky), use IRSA:

1. Create an IAM role that:
   - Has permission to call Bedrock (`bedrock:InvokeModel` etc.).
   - Trusts the EKS OIDC provider.
2. Create a Kubernetes ServiceAccount, annotated with that role ARN.
3. Configure your backend Deployment to use that ServiceAccount.

Then boto3 inside the backend pod **automatically** gets credentials from the pod’s IAM role. No static keys in Secrets.

If you are just experimenting and want something simpler (but less secure):

- Put access key & secret key in a Kubernetes Secret.
- Expose them as env vars for the backend pod.
- **Never** commit real keys to git or share them.

### Managing DB secrets

- For this demo, DB name/user/password live in `llm-secrets`.
- In production:
  - Prefer AWS Secrets Manager or SSM Parameter Store.
  - Use the Secrets Store CSI driver to mount them into pods.

---

## Part 5 – Summary of common edge cases

- **Backend cannot reach Postgres**:
  - Symptoms: logs show warnings like *“Could not connect to Postgres...”*.
  - App still returns LLM responses, but DB logging fails.
  - Check:
    - Service name (`llm-postgres`) and port (`5432`).
    - That StatefulSet pod is running.
- **Frontend cannot reach backend**:
  - In Docker:
    - Make sure `BACKEND_URL` is `http://backend:5000` inside the container.
  - In k8s:
    - Ensure `BACKEND_URL` matches the backend Service name + port (`llm-backend:5000`).
- **Bedrock permission errors**:
  - Error like `AccessDeniedException` from AWS.
  - Fix:
    - Ensure your IAM user/role has Bedrock permissions.
    - In EKS, verify IRSA role or env‑based keys.
- **LoadBalancer stuck in “pending”**:
  - Your AWS account might have VPC/subnet issues or load balancer quotas.
  - Check AWS console for events, or `kubectl describe svc llm-frontend`.

If you walk through `docs/01_overview.md` → `02_backend.md` → `03_frontend.md` → this file, you’ll have a full, end‑to‑end understanding of how the app works locally and on EKS, and how secrets and edge cases are handled.

