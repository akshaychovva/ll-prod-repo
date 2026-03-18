### 3. IAM and secrets management

This document explains how to give your components the **minimum permissions** they need and how to manage **sensitive data** (DB passwords, API keys) correctly.

---

### 3.1 Goals

- **No hard‑coded secrets** in code or AMIs.
- EC2 instances:
  - Can call **Bedrock**.
  - Can read **DB credentials** and other app config from a secure store.
  - Can use **SSM Session Manager** for shell access (no public SSH).
- Humans (you) have **limited, auditable** permissions.

We’ll use:

- **IAM Roles** for EC2 (instance profiles).
- **AWS Systems Manager Parameter Store** or **AWS Secrets Manager** for secrets.

---

### 3.2 Create an IAM role for EC2 app instances

1. Open the **IAM** console.
2. Go to **Roles → Create role**.
3. **Trusted entity**: AWS service.
4. **Use case**: `EC2`.
5. Click **Next** to attach policies.

Attach (or create) policies that allow:

- **Bedrock** access (example, customize to your needs):
  - Service: `bedrock`.
  - Actions (minimum to start):
    - `bedrock:InvokeModel`
    - `bedrock:InvokeModelWithResponseStream` (if you stream).
  - Resources: limit to specific model ARNs if you want, or start with `*` for learning, then tighten.

- **Systems Manager (SSM)** for Session Manager:
  - You can attach AWS‑managed policy:
    - `AmazonSSMManagedInstanceCore`

- **Secrets/parameter access**:
  - If you use **Parameter Store**:
    - Allow `ssm:GetParameter`, `ssm:GetParameters`, and `ssm:GetParametersByPath` on the paths you use.
  - If you use **Secrets Manager**:
    - Allow `secretsmanager:GetSecretValue` on your secret ARNs.

You can either:

- Use AWS‑managed policies where possible, plus
- Add a **custom inline policy** for your specific Bedrock + secrets resources.

Name the role something like:

- `prod-llm-app-ec2-role`

This role will later be attached to:

- The **Launch Template** used by your Auto Scaling Group.

---

### 3.3 Store DB credentials and app config in Parameter Store or Secrets Manager

You should not:

- Hard‑code DB passwords in:
  - Docker images.
  - AMIs.
  - Source code.

Instead use one of:

- **AWS Systems Manager Parameter Store**
  - Good for both non‑secret config and secrets.
  - Free/cheap and simple.
- **AWS Secrets Manager**
  - Adds rotation features and more secret‑focused capabilities.

We’ll use **Parameter Store** as an example.

#### 3.3.1 Create parameters in Parameter Store

1. Open **Systems Manager** in AWS console.
2. Go to **Parameter Store → Create parameter**.
3. For each piece of config, create a parameter, for example:

   - `/prod/llm-app/db/host`
   - `/prod/llm-app/db/port`
   - `/prod/llm-app/db/name`
   - `/prod/llm-app/db/user`
   - `/prod/llm-app/db/password`

   For **password**, choose type:

   - `SecureString`.

4. Optionally also store:

   - `/prod/llm-app/app/env` (e.g. `production`).
   - `/prod/llm-app/app/log-level` (e.g. `INFO`).
   - Any other config your app needs.

Make sure your IAM role from section 3.2 has permission to read `ssm:GetParameter` on `arn:aws:ssm:<region>:<account-id>:parameter/prod/llm-app/*`.

---

### 3.4 How app instances will read secrets/config

Inside your app’s startup script (or Docker Compose config), you can:

- Use the **AWS SDK** (Python `boto3`) to call Parameter Store and fetch needed values at startup, or
- Use the **SSM agent / EC2 User Data** to fetch parameters into environment variables, then start your containers with those env vars.

Conceptually:

1. EC2 instance boots with IAM role `prod-llm-app-ec2-role`.
2. At boot (via user data script) or at app start:
   - Call Parameter Store:

     ```bash
     aws ssm get-parameter --name "/prod/llm-app/db/password" --with-decryption --query "Parameter.Value" --output text
     ```

   - Export result as environment variables before launching Docker Compose.

3. The backend container reads DB host/user/password from environment variables.

This avoids:

- Embedding plaintext secrets in code or AMIs.

---

### 3.5 IAM for human users (you) – high level

To become “production‑ready” in thinking, treat even your own account carefully:

- Prefer to use an **individual IAM user** (or SSO) instead of root account.
- Give yourself:
  - Read/write for the specific services and resources you need (EC2, RDS, ALB, SSM, etc.).
  - Avoid broad `AdministratorAccess` in long‑term; use it only for initial learning and then tighten.

For now, during learning, you may keep broader permissions, but always keep in mind:

- In real production, IAM is heavily locked down and audited.

---

### 3.6 Checklist before moving on

Before you proceed to EC2 Auto Scaling and ALB, confirm:

1. You created **`prod-llm-app-ec2-role`** with:
   - Bedrock invocation permissions.
   - `AmazonSSMManagedInstanceCore`.
   - Read access to your SSM parameters (or Secrets Manager secrets).

2. You created **Parameter Store entries** for:
   - DB host, port, name, user, password.
   - Any app‑specific config you want.

3. You have a rough plan for how your **user data / startup script** on EC2 will:
   - Read parameters from SSM.
   - Export env vars.
   - Start Docker Compose (or your app) with those env vars.

Next: go to `04_ec2_auto_scaling_and_load_balancer.md` to wire up the **Auto Scaling Group + ALB** using this IAM role and your VPC subnets.

