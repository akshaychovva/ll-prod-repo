### 2. Create the EC2 instance (step by step in AWS Console)

This guide assumes:

- You have an AWS account.
- You can log in to the **AWS Management Console**.
- You are comfortable following screenshots / menus slowly.

We will:

1. Choose region.
2. Launch an EC2 instance.
3. Configure:
   - AMI
   - Instance type
   - Disk
   - Security group (ports 22 + 8501)
   - Key pair
   - IAM role with Bedrock permissions

---

### 2.1 Choose a region

1. Open the AWS Console in your browser.
2. On the top‑right, choose a **region** where:
   - Bedrock is available for you.
   - You plan to use EKS later (it’s nice to be consistent).

Example regions: `us-east-1` (N. Virginia) or `us-west-2` (Oregon), etc.

Make a note: **we will deploy EC2 + EKS in the same region.**

---

### 2.2 Open the EC2 service

1. In the AWS Console, search for **“EC2”** in the search bar.
2. Click **“EC2”**.
3. You will see the EC2 Dashboard.

---

### 2.3 Start the “Launch instance” wizard

1. On the EC2 Dashboard, click **“Launch instance”**.
2. You’ll see a form with multiple sections:
   - Name and tags
   - Application and OS Images (AMI)
   - Instance type
   - Key pair
   - Network settings
   - Configure storage
   - Advanced details (includes IAM role)

We’ll go section by section.

---

### 2.4 Name and AMI (OS Image)

- **Name**:
  - Set something like `bedrock-llm-demo-ec2`.

- **Application and OS Images (AMI)**:
  - Choose a **current Linux AMI**:
    - **Option A (recommended)**: `Amazon Linux 2023` (64‑bit x86).
    - **Option B**: `Ubuntu Server 22.04 LTS`.

We will assume **Amazon Linux 2023** in later commands. If you prefer Ubuntu, you just adjust package manager commands (`apt` instead of `dnf`).

---

### 2.5 Instance type (size)

For this demo, you need enough CPU/RAM to run:

- Postgres
- Flask backend
- Streamlit frontend

Good starting choices:

- `t3.small` (2 vCPU, 2 GB RAM) – OK but might be tight if many requests.
- `t3.medium` (2 vCPU, 4 GB RAM) – safer for experiments.

Select **`t3.small` or `t3.medium`** based on your free tier / cost preferences.

---

### 2.6 Key pair (for SSH)

1. In the **Key pair (login)** section:
   - If you **already have a key pair** in this region:
     - You can reuse it **if you have the `.pem` file** on your machine.
   - Otherwise, click **“Create new key pair”**.

2. When creating:
   - Name: `bedrock-ec2-key` (or anything).
   - Key pair type: `RSA`.
   - Private key file format: `pem`.

3. Click **“Create key pair”**:
   - Your browser will download a file like `bedrock-ec2-key.pem`.
   - **Store it carefully** on your local machine, e.g. `~/.ssh/bedrock-ec2-key.pem`.
   - Run:

   ```bash
   chmod 400 ~/.ssh/bedrock-ec2-key.pem
   ```

   This restricts permissions so SSH won’t complain.

---

### 2.7 Network settings – VPC, subnet, and Security Group

In the **Network settings** section:

1. **VPC**:
   - You can usually keep the **default VPC** for this simple setup.

2. **Subnet**:
   - Choose a public subnet (often the default selection is fine).

3. **Auto‑assign public IP**:
   - Make sure it is **Enabled**.
   - This gives your instance a **public IP address**, so you can SSH and open the app from your browser.

4. **Firewall (security group)**:
   - Choose **“Create security group”**.
   - Give it a name like `bedrock-ec2-sg`.

5. **Inbound security group rules**:

   You need at least:

   - **Rule 1 – SSH**
     - Type: `SSH`
     - Port: `22`
     - Source: your IP (e.g. `My IP` option) – **recommended**.

   - **Rule 2 – Streamlit UI**
     - Type: `Custom TCP`
     - Port range: `8501`
     - Source:
       - For dev/testing, you can set `My IP` (safer) or `0.0.0.0/0` (anywhere; not recommended for production).

   For a quick demo, setting both rules with **Source = My IP** is a good balance between convenience and safety.

---

### 2.8 Configure storage (disk)

In the **Configure storage** section:

- Set **size** to at least **30 GB** (gp3) to be comfortable with Docker images, logs, etc.
- Root volume type: `gp3` (default is fine).

For a demo, 20 GB may also work, but 30 GB gives more headroom.

---

### 2.9 IAM role (instance profile) – Bedrock permissions

In **Advanced details**, look for **IAM instance profile** or **IAM role**:

We want to **attach an IAM role** with **Bedrock permissions** to the instance.

There are two sub‑steps:

#### 2.9.1 Create an IAM role for EC2 (one‑time setup)

In a **separate tab**:

1. Open **IAM** in the AWS Console.
2. Go to **Roles**.
3. Click **“Create role”**.
4. **Trusted entity type**: AWS service.
5. **Use case**: Choose **EC2**.
6. Click **Next**.
7. **Permissions policies**:
   - Attach a policy that allows Bedrock invocation, e.g.:
     - If you have a custom policy, attach that.
     - Or create a new policy like:

       - Service: `bedrock`
       - Actions: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` (and any others you need).
       - Resources: ideally narrowed to specific ARN(s) of the model(s) you use.

8. Name the role, e.g. `bedrock-ec2-role`.
9. Create the role.

#### 2.9.2 Attach the role to your new EC2 instance

Back in the **Launch instance** wizard:

1. In **IAM instance profile / IAM role**, choose `bedrock-ec2-role` (or the name you picked).
2. This means **any code running on this EC2 instance**, including inside containers (if configured correctly), can call Bedrock **without static access keys**.

---

### 2.10 Final review and launch

Scroll down and click **“Launch instance”**.

AWS will:

- Create the EC2 instance.
- Attach the key pair, security group, IAM role, and disk.

Click **“View all instances”** to go to the Instances list.

You should see your instance with a state like **“Pending”**, then **“Running”**.

Make a note of:

- **Instance ID**.
- **Public IPv4 address** – we’ll use this for SSH and for the browser later.

---

### 2.11 Verify that the instance is running and reachable

From your local machine (where the `.pem` key is stored), try:

For Amazon Linux (default user is `ec2-user`):

```bash
ssh -i ~/.ssh/bedrock-ec2-key.pem ec2-user@<EC2_PUBLIC_IP>
```

For Ubuntu (default user is `ubuntu`):

```bash
ssh -i ~/.ssh/bedrock-ec2-key.pem ubuntu@<EC2_PUBLIC_IP>
```

If you see a shell prompt and can run:

```bash
uname -a
ls
```

…then your EC2 instance is ready. Next, go to `03_install_docker_and_clone_repo.md` to install Docker and get your app onto the instance.

