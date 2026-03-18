### 4. EC2 Auto Scaling Group and Application Load Balancer

Now we place your **application** inside the production‑style network you built:

- Create a **Launch Template** that knows how to boot an EC2 instance and start your app.
- Create an **Auto Scaling Group (ASG)** to keep N healthy instances running across AZs.
-- Create an **Application Load Balancer (ALB)** that receives traffic and forwards it to the ASG instances.

---

### 4.0 Important: when/where EC2 instances are actually created

You asked the key question: **“When do we initiate (launch) EC2 instances?”**

In a production‑style setup using Auto Scaling:

- You typically **do not click “Launch instance”** manually for app servers.
- Instead:
  - You create a **Launch Template** (the “recipe” for instances).
  - You create an **Auto Scaling Group** (the “manager” that maintains a fleet).
  - The moment you set **Desired capacity** (e.g. 2), the ASG will automatically **launch 2 EC2 instances** in your selected subnets.

So the “launch moment” is:

- **When you create the ASG** (or when you increase desired capacity later).

Where that happens:

- AWS Console: **EC2 → Auto Scaling groups → Create Auto Scaling group**
- After finishing the wizard:
  - The ASG starts creating EC2 instances immediately.

How your app gets onto those instances:

- On each instance boot, the **User Data** script in the Launch Template runs once.
  - That script is where you decide:
    - **Clone code** from Git (`git clone`), OR
    - **Pull images** from ECR (`docker pull ...`), OR
    - Use a **baked AMI** that already has everything.

This doc uses the learning‑friendly approach:

- Launch Template + User Data bootstrap (Pattern A).

---

### 4.1 Decide how the app will start on each instance

Every new EC2 instance in the ASG must:

1. Install Docker + Docker Compose (if not baked into an AMI).
2. Fetch config/secrets from SSM.
3. Get the app code (e.g. from Git or from an ECR image).
4. Start the app (e.g. via `docker compose up -d` or `docker run`).

There are two common patterns:

- **Pattern A – User Data bootstrap (simpler to start)**
  - Use a base AMI (e.g. Amazon Linux 2023).
  - In **User Data**, write a shell script that:
    - Installs Docker/Compose.
    - Pulls app images from ECR (or `git clone`s your repo).
    - Calls `aws ssm get-parameter ...` to fetch DB creds and config.
    - Starts the app containers.

- **Pattern B – Golden AMI (more advanced)**
  - Build a custom AMI that already has Docker + app binaries / images baked in.
  - ASG boots faster and user data is smaller.

For learning, **Pattern A** is enough and teaches you how user data works.

---

### 4.1.1 Instance lifecycle (what happens after ASG launches EC2)

When you set ASG Desired capacity = 2, the following happens automatically:

1. **ASG creates EC2 instances**
   - In your chosen **private app subnets** (across 2 AZs).
   - With your chosen instance type and disk.

2. **Instance boots** (OS starts)

3. **User Data runs (first boot only)**
   - Installs Docker, awscli, etc.
   - Pulls configuration from SSM (Parameter Store / Secrets Manager).
   - Gets your application (clone/pull images).
   - Starts the app containers.

4. **App starts listening on an internal port**
   - Example: Streamlit may listen on port 8501.
   - You might run a reverse proxy (Nginx) and expose port 80 locally on the instance.

5. **ALB health checks begin**
   - ALB hits the target group health check path.
   - Instance is marked:
     - `unhealthy` while bootstrapping,
     - then `healthy` once your app is ready.

6. **ALB routes traffic only to healthy instances**

This is why:

- In production you don’t SSH and start containers manually.
- You make boot predictable by putting everything into:
  - **Launch Template configuration** + **User Data** (or a baked AMI).

---

### 4.2 Create a Launch Template

1. In the **EC2 console**, go to **Launch templates**.
2. Click **“Create launch template”**.

Fill fields:

- **Launch template name**: `prod-llm-app-template`.
- **Template version description**: `v1 bootstrap app via user data`.

Under **Application and OS Images (AMI)**:

- Choose e.g. **Amazon Linux 2023**.

Under **Instance type**:

- Choose something like `t3.small` or `t3.medium` (similar to earlier EC2).

Under **Key pair**:

- You can leave it **None** if you plan to use **SSM Session Manager** only.
  - If you want temporary SSH access, you can specify a key pair.

Under **Network settings**:

- Do **not** hard‑code a specific subnet here; the ASG will handle subnets.
- For **Security groups**, select:
  - `prod-llm-app-sg` (created in the networking step).

Under **Resource tags**:

- Add tags like:
  - `Name = prod-llm-app-ec2`.
  - `Environment = production` (or `dev`, depending on what you’re building).

Under **Advanced details**:

- **IAM instance profile**: choose `prod-llm-app-ec2-role`.
- **User data**: paste a bootstrap script (example below).

Example **user data** (very simplified starting point, for Amazon Linux 2023, using ECR images and Parameter Store; adjust URLs/names to your setup):

```bash
#!/bin/bash
set -xe

# 1) Update and install basics
dnf update -y
dnf install -y docker awscli docker-compose-plugin git
systemctl enable docker
systemctl start docker

# 2) Fetch DB config from SSM Parameter Store
REGION="<your-region>"  # e.g. us-east-1
APP_PATH="/prod/llm-app"

DB_HOST=$(aws ssm get-parameter --name "$APP_PATH/db/host" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_PORT=$(aws ssm get-parameter --name "$APP_PATH/db/port" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_NAME=$(aws ssm get-parameter --name "$APP_PATH/db/name" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_USER=$(aws ssm get-parameter --name "$APP_PATH/db/user" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_PASSWORD=$(aws ssm get-parameter --name "$APP_PATH/db/password" --with-decryption --query "Parameter.Value" --output text --region "$REGION")

# 3) Export env vars so Docker sees them
cat <<EOF >/etc/profile.d/llm-app-env.sh
export DB_HOST="$DB_HOST"
export DB_PORT="$DB_PORT"
export DB_NAME="$DB_NAME"
export DB_USER="$DB_USER"
export DB_PASSWORD="$DB_PASSWORD"
export AWS_REGION="$REGION"
EOF

source /etc/profile.d/llm-app-env.sh

# 4) Get app code or images
cd /opt
git clone https://github.com/<your-username>/<your-repo>.git app   # or pull images from ECR
cd app

# 5) Start app via Docker Compose (assumes docker-compose.yml reads env vars)
docker compose up --build -d
```

You will later refine this script (e.g. use ECR, error handling, logging).

Click **Create launch template**.

---

### 4.3 Create an Auto Scaling Group (ASG)

1. In the **EC2 console**, go to **Auto Scaling Groups**.
2. Click **“Create Auto Scaling group”**.

Basic configuration:

- **Auto Scaling group name**: `prod-llm-app-asg`.
- **Launch template**: select `prod-llm-app-template`.

Network:

- **VPC**: choose your `prod-llm-vpc`.
- **Subnets**: select **both private app subnets** (e.g. `prod-llm-private-app-a` and `prod-llm-private-app-b`).

Load balancing:

- We’ll attach an **Application Load Balancer**:
  - Choose **“Attach to an existing load balancer”** only after ALB is created, or
  - **“Attach to a new load balancer”** and follow the wizard from here (see next section for ALB config).

Group size and scaling:

- For learning:
  - **Desired capacity**: 2 instances.
  - **Minimum capacity**: 2.
  - **Maximum capacity**: 4 (or more depending on budget).

Health checks:

- Use **EC2 and ELB** health checks.

Scaling policies:

- Start with **none** or a simple target tracking policy (e.g. keep average CPU around 50%).

Tags:

- Add `Environment = prod`, `App = llm-demo`, etc.

Complete the wizard. Your ASG will now keep the desired number of instances running across the private subnets.

Immediately after ASG creation:

- Go to **EC2 → Instances** and you will see **2 new EC2 instances** launching.
- These are your “app servers” managed by the ASG.

---

### 4.4 Create an Application Load Balancer (ALB)

If you didn’t create the ALB during the ASG wizard, do it now.

1. In the **EC2 console**, go to **Load balancers**.
2. Click **“Create load balancer”** → **Application Load Balancer**.

Basic configuration:

- **Name**: `prod-llm-alb`.
- **Scheme**: `internet-facing`.
- **IP address type**: IPv4.

Network:

- **VPC**: `prod-llm-vpc`.
- **Mappings**: choose your **public subnets** in 2 AZs.

Security groups:

- Attach `prod-llm-alb-sg`.

Listeners and routing:

- Listener:
  - Protocol: `HTTP`.
  - Port: `80`.

- Target group:
  - Create a **new target group**:
    - Type: `Instances`.
    - Target group name: `prod-llm-app-tg`.
    - Protocol: `HTTP`.
    - Port: app port on instances (e.g. `80` or `8501` – match what your app listens on).
    - Health checks:
      - Protocol: `HTTP`.
      - Path: health endpoint of your app (e.g. `/healthz` or `/` if simple).

After target group creation, **attach the ASG** as a registered target **or** configure the ASG to use this target group:

- In ASG settings:
  - Set the **target group** to `prod-llm-app-tg`.

Now ALB will:

- Accept HTTP traffic on port 80 from the internet.
- Forward requests to instances in the target group (your ASG instances).
- Use health checks to route only to healthy instances.

---

### 4.4.1 Where Streamlit port 8501 fits with an ALB (important)

ALB forwards traffic to an **instance port** in the target group.

You have two common choices:

- **Choice A (simplest)**: ALB forwards to **8501** on instances
  - Target group port = 8501
  - Instances listen on 8501
  - Works, but you are effectively exposing Streamlit directly behind ALB.

- **Choice B (more production‑style)**: run a reverse proxy (Nginx) on instances
  - Nginx listens on port **80** on the instance.
  - Nginx proxies to Streamlit on **8501** locally.
  - Target group port = 80
  - This is cleaner if you later want:
    - Multiple paths (/api vs /),
    - Better headers/timeouts,
    - Easier TLS patterns.

For learning quickly, Choice A is fine. For production skills, Choice B is a good next step.

---

### 4.5 Test the ALB and scaling behavior

Once the ASG has launched instances and user data has run:

1. In the **Load balancers** list, copy the **DNS name** of `prod-llm-alb`, e.g.:

   ```text
   http://prod-llm-alb-1234567890.us-east-1.elb.amazonaws.com
   ```

2. Open it in a browser.

If everything is wired correctly:

- You should see the same Streamlit UI (or app) as before, but now behind ALB.
- If one instance is terminated:
  - ASG will launch a new one.
  - ALB health checks will temporarily mark it as unhealthy, then healthy once app is ready.

---

### 4.6 Summary – what this step gave you

You now have:

- A **Launch Template** that knows how to:
  - Boot EC2 with your app role.
  - Install Docker + start your app via user data.
- An **Auto Scaling Group** that:
  - Keeps N instances across AZs.
  - Can be configured to scale up/down on metrics.
- An **Application Load Balancer** that:
  - Exposes a single DNS endpoint.
  - Spreads traffic across instances.
  - Uses health checks to avoid unhealthy instances.

This is a huge step toward production‑style operations.

Next: in `05_database_and_storage_strategy.md`, you’ll move your database from local/container into **Amazon RDS**, and wire your app to it properly.

