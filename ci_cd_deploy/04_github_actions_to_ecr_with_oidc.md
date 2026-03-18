### 4. GitHub Actions → AWS (OIDC) → ECR (best practice)

This is the most important CI/CD security concept:

- **Do not store AWS access keys in GitHub secrets** if you can avoid it.
- Use **OIDC** (OpenID Connect) so GitHub Actions can assume an AWS role securely.

This section explains exactly what to create in AWS and what to add to GitHub.

---

### 4.1 What is OIDC (simple explanation)

OIDC lets GitHub prove to AWS:

- “This workflow run is from repo X, branch Y, workflow Z.”

Then AWS allows it to assume a specific IAM role.

So:

- No long‑lived keys.
- Short‑lived credentials per workflow run.
- Better security, closer to real production.

---

### 4.2 Create the GitHub OIDC identity provider in AWS (one time)

1. Open AWS Console → **IAM**.
2. Go to **Identity providers**.
3. Click **Add provider**.
4. Select:
   - Provider type: **OpenID Connect**
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
5. Add the provider.

This allows AWS to trust tokens issued by GitHub Actions.

---

### 4.3 Create an IAM role for GitHub Actions (push to ECR)

1. IAM → Roles → **Create role**
2. Trusted entity:
   - **Web identity**
3. Identity provider:
   - Select the GitHub provider you created above.
4. Audience:
   - `sts.amazonaws.com`

Now you must restrict which GitHub repos/branches can assume this role.

#### 4.3.1 Trust policy (important)

In the role trust policy, restrict to your repo, for example:

- repo: `<your-org-or-user>/<your-repo>`
- branch: `main`

Conceptually, conditions look like:

- `token.actions.githubusercontent.com:sub` equals:
  - `repo:<owner>/<repo>:ref:refs/heads/main`

This ensures only that repo/branch can use the role.

Name the role:

- `GithubActionsECRPushRole`

#### 4.3.2 Permissions policy for the role

Attach a policy that allows:

- ECR authentication and push operations:
  - `ecr:GetAuthorizationToken`
  - `ecr:BatchCheckLayerAvailability`
  - `ecr:CompleteLayerUpload`
  - `ecr:InitiateLayerUpload`
  - `ecr:PutImage`
  - `ecr:UploadLayerPart`
  - `ecr:BatchGetImage` (sometimes needed)
  - `ecr:DescribeRepositories` (optional)

Scope it to your repositories if you want strict least privilege:

- `llm-app-backend`
- `llm-app-frontend`

For learning, you can start slightly broader then tighten later.

---

### 4.4 Add GitHub Actions workflow to build and push images

In your GitHub repo, create:

- `.github/workflows/build-and-push.yml`

This workflow should:

1. Checkout code.
2. Configure AWS creds via OIDC (assume the role).
3. Login to ECR.
4. Build backend image and push to ECR with tags:
   - `${{ github.sha }}`
   - optional `latest`
5. Build frontend image and push similarly.

Minimal example (you must replace placeholders):

```yaml
name: Build and push images to ECR

on:
  push:
    branches: [ "main" ]

permissions:
  id-token: write
  contents: read

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    env:
      AWS_REGION: us-east-1
      ACCOUNT_ID: "123456789012"
      BACKEND_REPO: "llm-app-backend"
      FRONTEND_REPO: "llm-app-frontend"

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GithubActionsECRPushRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push backend
        run: |
          IMAGE="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}"
          docker build -f backend/Dockerfile -t "${IMAGE}:${GITHUB_SHA}" .
          docker push "${IMAGE}:${GITHUB_SHA}"

      - name: Build and push frontend
        run: |
          IMAGE="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${FRONTEND_REPO}"
          docker build -f frontend/Dockerfile -t "${IMAGE}:${GITHUB_SHA}" .
          docker push "${IMAGE}:${GITHUB_SHA}"
```

Why we use `${GITHUB_SHA}`:

- It creates an immutable version you can deploy and roll back to safely.

---

### 4.5 Verify the pipeline worked

After pushing to `main`:

1. Open GitHub → Actions tab.
2. Confirm the workflow succeeded.
3. Open AWS → ECR → your repo → **Images**.
4. You should see a new tag equal to the commit SHA.

If you see images in ECR, CI is done.

Next step is CD: getting EC2 instances to run that new tag.

Next: `05_ec2_bootstrap_pull_from_ecr.md`.

