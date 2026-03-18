### 7. Optional: Blue/Green deployments (safer than rolling)

Rolling deployments (Instance Refresh) are great and common. Blue/Green is an extra safety step:

- You run the new version (green) separately.
- You test it.
- Then you switch traffic from old (blue) → new (green) quickly.

---

### 7.1 What “blue” and “green” mean

- **Blue**: current production environment (ASG + target group).
- **Green**: new environment running the new version (ASG + target group).

ALB can route traffic to either target group.

---

### 7.2 Setup (one time)

You need:

- One ALB
- Two target groups:
  - `prod-llm-app-blue-tg`
  - `prod-llm-app-green-tg`
- Two ASGs:
  - `prod-llm-app-blue-asg`
  - `prod-llm-app-green-asg`

Each ASG attaches to its own target group.

---

### 7.3 Deployment flow (step by step)

1. **Blue is live**
   - ALB listener forwards 100% traffic to blue target group.

2. **Deploy green**
   - Update green ASG launch template / release tag to new version.
   - Ensure green instances boot and become healthy in green target group.

3. **Test green**
   - Option A: temporarily route a small percentage to green (canary).
   - Option B: expose a separate test listener rule or path to reach green.

4. **Switch traffic**
   - Change ALB listener rules so 100% goes to green.

5. **Keep blue for quick rollback**
   - If green fails, switch back to blue instantly.

6. **Cleanup**
   - After confidence, either:
     - scale blue to 0, or
     - keep it as standby.

---

### 7.4 Why blue/green is valuable

- Fast rollback (route traffic back to blue in seconds).
- Lets you test green without affecting all users.
- Great when you’re not fully confident in health checks alone.

---

### 7.5 When you should use it

Use blue/green when:

- Deployments are risky.
- You need near‑zero downtime.
- You want safer rollouts than rolling refresh.

For learning and small projects, rolling refresh is usually enough, but blue/green is a great DevOps skill to understand.

