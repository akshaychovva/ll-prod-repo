### 6. Deploy to EC2 safely using ASG Instance Refresh (rolling deployment)

This is the most practical “production” deployment mechanism with:

- Application Load Balancer (ALB)
- Auto Scaling Group (ASG)

Goal:

- Roll out new versions gradually
- Keep the site up
- Use health checks to prevent broken versions from taking traffic

---

### 6.1 What “Instance Refresh” means

An **Instance Refresh** tells an ASG:

- “Replace instances gradually, using the latest Launch Template config.”

Process:

1. ASG launches a new instance.
2. New instance runs user data (pull images, start containers).
3. ALB health checks it.
4. Only after it becomes healthy:
   - ASG terminates an old instance.
5. Repeat until all instances are replaced.

Why it’s production‑ready:

- You never take down all servers at once.
- Health checks are used to prevent bad instances from receiving traffic.

---

### 6.2 Choose what changes during a deploy (two models)

You can deploy by changing:

#### Model A (recommended): update the SSM “release tag” parameter

- Update `/prod/llm-app/release/imageTag` from old SHA → new SHA.
- Then run Instance Refresh.
- New instances will read the parameter and pull that version.

Pros:

- Very simple to rollback: set parameter back to previous SHA and refresh again.

#### Model B: create a new Launch Template version per release

- Update user data to use a specific tag baked into it.
- Create new LT version.
- Instance Refresh.

Pros:

- Strong immutability at the infra level.

Cons:

- More template versions and more automation required.

This guide assumes **Model A**.

---

### 6.3 Step-by-step: deploy a new version (Model A)

You have:

- New images pushed to ECR with tag = commit SHA (from GitHub Actions).

Now deploy:

#### Step 1: pick the new tag

- In GitHub Actions output, note the commit SHA used.
- Or in AWS ECR, find the image tag you want.

Let’s call it:

- `NEW_TAG=<new-commit-sha>`
- `OLD_TAG=<old-commit-sha>`

#### Step 2: update the “current release” SSM parameter

In AWS Console:

1. Systems Manager → Parameter Store
2. Find `/prod/llm-app/release/imageTag`
3. Edit → set value to `NEW_TAG`
4. Save

Why:

- This is your “production pointer”.

#### Step 3: start an Instance Refresh

In AWS Console:

1. EC2 → Auto Scaling Groups
2. Select `prod-llm-app-asg`
3. Go to **Instance refresh**
4. Click **Start instance refresh**

Choose settings like:

- **Minimum healthy percentage**: 90 (or 100 if you can temporarily over‑provision)
- **Instance warmup**: 300 seconds (5 minutes) to allow user data + app boot

Start.

#### Step 4: monitor health during rollout

Watch in parallel:

- EC2 → Instances: new instances coming up
- EC2 → Target groups → `prod-llm-app-tg` → Targets:
  - New targets move from:
    - initial → unhealthy → healthy
- ALB metrics:
  - 5xx errors
  - latency
- CloudWatch Logs (if enabled)

Instance Refresh is successful when:

- All instances are replaced,
- All targets are healthy,
- No spikes in errors/latency.

---

### 6.4 How rollback works (fast and simple)

If you see errors during rollout:

1. Stop the instance refresh (ASG console).
2. Set `/prod/llm-app/release/imageTag` back to `OLD_TAG`.
3. Start a new instance refresh.

This is why immutable image tags + a release pointer is powerful:

- Rollback is a single parameter change.

---

### 6.5 Common reasons deployments fail (and what it looks like)

If new targets never become healthy:

- User data might be failing:
  - ECR login/pull errors
  - SSM parameter permission errors
  - App crash due to wrong env vars
- Health check path/port mismatch:
  - ALB checks `/healthz` but your app doesn’t serve it
  - Target group port set to 80 but app listens on 8501 (or vice versa)

Debugging:

- Check EC2 system logs / user data output.
- Use SSM Session Manager to log into the instance and:
  - `docker ps`
  - `docker logs <container>`

---

### 6.6 Summary

You now have a production‑style deployment loop:

1. Merge/push code → CI builds and pushes images to ECR
2. Update release pointer in SSM
3. ASG Instance Refresh rolls out new instances
4. ALB health checks protect traffic
5. Rollback is “change pointer back”

Next: `07_optional_blue_green.md` if you want an even safer deployment model.

