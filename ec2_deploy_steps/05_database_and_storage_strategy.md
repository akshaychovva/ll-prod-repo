### 5. Database and storage strategy (RDS Postgres)

Running Postgres in a container on a single EC2 instance is fine for demos, but not ideal for production. In this step you’ll:

- Move the database to **Amazon RDS for Postgres**.
- Place it in the **DB private subnets** of your VPC.
- Use **security groups + SSM parameters** to connect your app securely.
- Configure **backups and Multi‑AZ**.

---

### 5.1 Why RDS instead of containerized DB

RDS gives you:

- Automated backups and point‑in‑time recovery.
- Optional Multi‑AZ for high availability.
- Automatic minor version patching windows.
- Monitoring metrics out of the box.

This reduces the operational burden and is standard in many production setups.

---

### 5.2 Create RDS subnet group

1. Open the **RDS** console.
2. Go to **Subnet groups → Create DB subnet group**.

Fill:

- **Name**: `prod-llm-db-subnet-group`.
- **Description**: `Prod LLM app RDS subnets`.
- **VPC**: `prod-llm-vpc`.
- **Subnets**:
  - Select the two **private DB subnets** (`prod-llm-private-db-a`, `prod-llm-private-db-b`).

Create the subnet group.

---

### 5.3 Create an RDS Postgres instance

1. In RDS console, go to **Databases → Create database**.
2. Choose:
   - **Standard create**.
   - **Engine**: PostgreSQL.

Templates:

- For learning, you can pick “Free tier” if available, or a small dev instance class.

Settings:

- **DB instance identifier**: `prod-llm-postgres`.
- **Master username**: e.g. `llm_user`.
- **Master password**: choose a strong password (you will store it in SSM).

Instance configuration:

- **DB instance class**: a small class like `db.t3.micro` or `db.t3.small` (depending on free tier/limits).

Storage:

- Start with e.g. 20–50 GB General Purpose (gp3).

Connectivity:

- **Compute resource**: “Don’t connect to an EC2 compute resource” (we already have our own ASG).
- **VPC**: `prod-llm-vpc`.
- **DB subnet group**: `prod-llm-db-subnet-group`.
- **Public access**: `No` (private only).
- **VPC security group**:
  - Choose **existing** and select `prod-llm-db-sg`.

Additional configuration:

- **Initial database name**: `llm_db` (or similar).
- **Backup retention**: choose a few days (e.g. 7) for learning; more in real production.
- **Multi‑AZ**: enable if you want to practice HA (costs more; optional for learning).

Create the database.

Wait until the instance status is **Available**.

---

### 5.4 Store DB connection info in Parameter Store

When the DB is available, note:

- **Endpoint** (e.g. `prod-llm-postgres.xxxxxx.region.rds.amazonaws.com`).
- **Port** (usually 5432).
- **DB name** (e.g. `llm_db`).
- **Master username/password**.

Update your Parameter Store entries (or create new ones) to match:

- `/prod/llm-app/db/host` = `<RDS endpoint>`
- `/prod/llm-app/db/port` = `5432`
- `/prod/llm-app/db/name` = `llm_db`
- `/prod/llm-app/db/user` = `llm_user`
- `/prod/llm-app/db/password` = `<the master password>` (as `SecureString`)

Your EC2 app instances will fetch these values via SSM as described earlier.

---

### 5.5 Update app configuration to use RDS

Your backend’s DB connection string should now point to `prod-llm-postgres` instead of a local container.

Make sure:

- Environment variables (or config) on the app instance read from SSM and map to whatever your backend expects (e.g. `DB_HOST`, `DB_USER`, etc.).
- Ports and SSL options match the RDS configuration (you can start with non‑SSL for dev, then enable SSL in real production).

When you deploy a new version or restart instances:

- User data (or app bootstrap) will:
  - Retrieve updated SSM parameters.
  - Connect to RDS instead of localhost.

---

### 5.6 Migrations and initial schema

To be production‑ready, DB schema management should be explicit:

- Use a migration tool (e.g. Alembic, Flyway, Liquibase, Django migrations, etc.) to:
  - Create tables.
  - Apply schema changes.

Process example:

1. Build a container or script that:
   - Reads the same DB env vars.
   - Runs migrations at deploy time or on demand.
2. When you first point your app to RDS:
   - Run the migration tool once to create schema.

This is more robust than relying on ad‑hoc SQL scripts or ORM auto‑create in production.

---

### 5.7 Backups and recovery considerations

In the RDS DB instance settings:

- **Automated backups**:
  - Ensure retention is non‑zero (e.g. 7+ days).
  - This allows point‑in‑time recovery.

- **Snapshots**:
  - You can create manual snapshots before major schema changes or deployments.

- **Multi‑AZ**:
  - If enabled, RDS keeps a synchronous standby in another AZ.
  - In case of AZ failure, it can fail over automatically.

As a DevOps engineer, you should:

- Know where backups are configured.
- Practice (at least once) a test restore into a **non‑prod** environment.

---

### 5.8 Checklist before moving on

Before you tackle CI/CD and observability, confirm:

1. **RDS Postgres** is running in `prod-llm-vpc` with:
   - Subnet group using private DB subnets.
   - Security group `prod-llm-db-sg`.
2. **Parameter Store** entries for DB connection are updated with RDS values.
3. Your EC2 instances (in the ASG) can:
   - Reach the RDS endpoint on port 5432 (due to SG rules).
   - Successfully initialize the DB connection at app startup.

Next: go to `06_ci_cd_and_deployment_strategy.md` to make builds and deployments more **repeatable and automated**, which is critical for production‑ready DevOps.

