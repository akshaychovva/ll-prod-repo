### 7. Observability – logging, metrics, and alerting

To be a production‑ready DevOps engineer, you must be able to **see** what the system is doing and be **notified** when things go wrong.

This doc focuses on:

- Centralizing logs.
- Tracking metrics and setting alarms.
- Having basic runbooks for common issues.

---

### 7.1 Centralized logging with CloudWatch Logs

Right now, your app logs likely stay on each EC2 instance (e.g. `docker logs` or local files). In production, you want logs to go to **CloudWatch Logs** so you can:

- Search across all instances.
- Correlate errors with deployments or traffic spikes.

Options:

- **Option A – CloudWatch Logs agent on each EC2 instance**
  - Install and configure agent to watch:
    - Docker logs directory (e.g. `/var/lib/docker/containers/...`).
    - Or application log files.

- **Option B – Docker logging driver**
  - Configure Docker to send logs directly to CloudWatch Logs.

For learning, Option A (CloudWatch agent) is a good start.

Steps (high‑level):

1. Install the CloudWatch agent via user data or SSM.
2. Configure it with a JSON config that:
   - Sends app logs to a log group like `/prod/llm-app/application`.
   - Sends system logs to `/prod/llm-app/system`.
3. Ensure the EC2 IAM role has permissions:
   - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`.

Result:

- All app instances write into the same log groups, with different log streams per instance.

---

### 7.2 Metrics and dashboards (CloudWatch)

CloudWatch automatically collects metrics such as:

- EC2: CPU, network, disk.
- RDS: CPU, connections, free storage, etc.
- ALB: request count, target response time, 4xx/5xx counts.

As DevOps, you should:

1. Create a **CloudWatch dashboard** that shows:
   - ALB metrics:
     - Requests per minute.
     - Target response time.
     - 4xx/5xx error counts.
   - EC2 metrics:
     - CPU utilization for the ASG.
   - RDS metrics:
     - CPU utilization.
     - Database connections.
     - Free storage space.

2. Watch the dashboard during:
   - Load tests.
   - Deployments.
   - Incident simulations.

This helps you build intuition about how the system behaves.

---

### 7.3 Alarms and notifications

Use **CloudWatch Alarms + SNS** to get alerts when something important goes wrong.

Example alarms to start with:

- **High error rate on ALB**
  - Metric: `HTTPCode_Target_5XX_Count` for your ALB/target group.
  - Alarm if 5xx errors > X per minute for Y minutes.

- **High latency**
  - Metric: `TargetResponseTime` for ALB.
  - Alarm if p95 or p99 latency exceeds a threshold.

- **High CPU on ASG**
  - Metric: average EC2 CPU Utilization for ASG.
  - Alarm if > 80% for several minutes.

- **RDS abnormal metrics**
  - High CPU.
  - Low free storage.
  - Too many connections.

Each alarm should:

- Send a notification to an **SNS topic** with:
  - Email subscription (your email).
  - Later, maybe Slack/Webhook integration.

This way you:

- Know when to log in and investigate.
- Don’t have to manually watch the dashboard all the time.

---

### 7.4 Basic runbooks (how you respond to issues)

For each alarm type, write a **short runbook** – a checklist you follow when the alarm fires.

Example: **High 5xx errors on ALB**

1. Check app logs in CloudWatch:
   - Filter by `ERROR` or relevant patterns.
2. Check recent deployments:
   - Did a new version go out just before the spike?
3. Check RDS status:
   - Is the DB reachable and healthy?
4. Roll back if needed:
   - Use ASG + Launch Template to roll back to the previous stable image tag.

Example: **High CPU on ASG**

1. Check if it’s **legitimate traffic** (marketing campaign, etc.).
2. If yes, **scale out**:
   - Temporarily increase ASG max capacity, or
   - Adjust auto‑scaling policy thresholds.
3. If it’s a bug (infinite loop, memory leak):
   - Capture logs and metrics.
   - Fix the code and deploy a new version.

Having even a **one‑page runbook** per alarm trains you to think like a production engineer.

---

### 7.5 Cost awareness

Part of being production‑ready is understanding **cost impact**:

- ALB, NAT gateways, RDS, and ASG instances all cost money.
- Alarms and dashboards are cheap but important.

As you experiment:

- Use **billing console** and **Cost Explorer** to monitor:
  - Daily spend.
  - Which services cost the most.

Turn off or scale down resources when not in use:

- Reduce ASG desired capacity.
- Stop RDS instances (for dev, not prod).
- Delete unused ALBs or NAT gateways.

---

### 7.6 Summary – operating like a DevOps engineer

With observability in place, you:

- See logs from all instances in one place.
- Watch metrics and dashboards for trends.
- Get alerted when key metrics go out of range.
- Have runbooks to respond in a structured way.

Combined with the previous steps (networking, IAM, ASG, ALB, RDS, CI/CD), you are now following many of the same patterns real **DevOps/SRE teams** use to run production systems on EC2.

