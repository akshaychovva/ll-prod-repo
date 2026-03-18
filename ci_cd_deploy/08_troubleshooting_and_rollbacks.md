### 8. Troubleshooting and rollbacks (CI/CD + EC2)

This guide helps you debug the most common points of failure in the pipeline:

- GitHub Actions
- ECR authentication/push
- EC2 bootstrapping (user data)
- SSM parameters and IAM permissions
- ALB target group health checks

And it gives you a simple rollback playbook.

---

### 8.1 CI fails before push

Symptoms:

- GitHub Actions job fails during build.

What to check:

- Docker build context is correct (Dockerfile path, build root).
- Dependencies download correctly (network).
- Your Dockerfiles build locally:

  ```bash
  docker build -f backend/Dockerfile .
  docker build -f frontend/Dockerfile .
  ```

Fix:

- Fix Dockerfile or dependencies, commit again, re‑run pipeline.

---

### 8.2 CI cannot authenticate to AWS / cannot push to ECR

Symptoms:

- “Not authorized to perform sts:AssumeRoleWithWebIdentity”
- “denied: User is not authorized to perform ecr:PutImage”

What to check:

- IAM identity provider exists in AWS:
  - `https://token.actions.githubusercontent.com`
- IAM role trust policy matches your repo and branch:
  - `repo:<owner>/<repo>:ref:refs/heads/main`
- Role has ECR push permissions.
- GitHub workflow has permissions:
  - `id-token: write`
  - `contents: read`

Fix:

- Correct trust policy conditions and retry.

---

### 8.3 Images exist in ECR, but EC2 instances can’t pull them

Symptoms:

- User data runs but containers don’t start.
- Instances show healthy at EC2 level but unhealthy in target group.

What to check:

- EC2 instance role has ECR pull permissions:
  - `ecr:GetAuthorizationToken`
  - `ecr:BatchGetImage`
  - `ecr:GetDownloadUrlForLayer`
  - `ecr:BatchCheckLayerAvailability`
- Instances can reach ECR network endpoints:
  - Private subnets need NAT gateway (or VPC endpoints for ECR).

Fix:

- Add missing IAM permissions.
- Ensure NAT routes exist for private app subnets.

---

### 8.4 User data script failing (most common!)

Symptoms:

- EC2 instance launched, but app is not running.
- Target group health check fails.

What to check:

- User data output/logs:
  - In EC2 console: Instance → **System log**.
  - Or check cloud-init logs via SSM session:
    - `/var/log/cloud-init-output.log`

Typical causes:

- A single command fails and stops the script.
- Wrong region/account ID in script.
- Missing SSM parameter name or wrong path.
- Docker service not started.

Fix strategy:

- Add `set -xe` (or `set -euo pipefail`) to user data so it fails fast with logs.
- Keep script small and test incrementally.

---

### 8.5 ALB health check failures (port/path mismatch)

Symptoms:

- Instances are running, but target group shows unhealthy.

What to check:

- Target group port equals the port your app is listening on (instance side).
- Health check path exists:
  - If you use `/healthz`, your app must return 200 there.
  - For early learning, you can use `/` if it returns 200.

Fix:

- Align:
  - instance container ports,
  - security group inbound rules,
  - target group port,
  - health check path.

---

### 8.6 Simple rollback playbook (use this when you panic)

Assuming you use the SSM release pointer approach:

1. Identify last known good tag:
   - `OLD_TAG`
2. In SSM Parameter Store:
   - Set `/prod/llm-app/release/imageTag` back to `OLD_TAG`
3. In ASG:
   - Start Instance Refresh to roll back instances
4. Watch:
   - Target group health
   - ALB 5xx
   - Logs

You are back to a known good version.

---

### 8.7 Debugging checklist (fast)

If “the site is down”:

1. ALB DNS works?
2. Target group: any healthy targets?
3. ASG: how many instances running?
4. One instance: SSM shell → `docker ps` → logs
5. SSM parameters correct?
6. IAM permissions correct?

This order narrows the issue quickly.

