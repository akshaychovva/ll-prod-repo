### 3. Install Docker and get this project onto the EC2 instance

Now that your EC2 instance is running and you can SSH into it, we will:

1. Update the OS packages.
2. Install **Docker**.
3. Enable and start the Docker service.
4. Install **Docker Compose plugin** (so we can run `docker compose`).
5. Get **this project** onto the instance:
   - Either via `git clone`, or
   - By copying your local folder with `scp`.

> These steps assume **Amazon Linux 2023**. If you chose Ubuntu, the commands are similar but use `apt` instead of `dnf`.

---

### 3.1 SSH into the EC2 instance

From your local machine:

```bash
ssh -i ~/.ssh/bedrock-ec2-key.pem ec2-user@<EC2_PUBLIC_IP>
```

Replace `<EC2_PUBLIC_IP>` with the public IP from the EC2 console.

You should see a prompt like:

```bash
[ec2-user@ip-... ~]$
```

---

### 3.2 Update packages (Amazon Linux 2023)

Run:

```bash
sudo dnf update -y
```

This ensures your packages and security patches are up to date.

---

### 3.3 Install Docker engine

On Amazon Linux 2023:

```bash
sudo dnf install -y docker
```

Enable the Docker service to start on boot:

```bash
sudo systemctl enable docker
```

Start Docker now:

```bash
sudo systemctl start docker
```

Check that Docker is running:

```bash
sudo docker ps
```

You should see no containers (empty list) but **no error**.

Optionally, add your user (`ec2-user`) to the `docker` group so you don’t have to type `sudo` every time:

```bash
sudo usermod -aG docker ec2-user
```

Then **log out and log back in** for the group change to take effect.

---

### 3.4 Install Docker Compose plugin

Modern Docker uses **`docker compose`** (with a space) via a plugin.

On Amazon Linux 2023, you can often install it with:

```bash
sudo dnf install -y docker-compose-plugin
```

Verify:

```bash
docker compose version
```

If the command prints a version (e.g. `Docker Compose version v2.x`), you’re good.

If you see an error, you can instead install via the official binary (example):

```bash
DOCKER_COMPOSE_VERSION=v2.27.0
sudo curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version
```

In that case, you would run `docker-compose` instead of `docker compose`. For consistency with your project, we prefer the **plugin approach** if available.

---

### 3.5 Option A – Clone the repo from Git

If your project is in a Git repo that EC2 can access (e.g. GitHub, CodeCommit), the simplest method is:

1. Install `git`:

   ```bash
   sudo dnf install -y git
   ```

2. Choose a directory (e.g. your home directory):

   ```bash
   cd ~
   ```

3. Clone the repo (example – replace with your actual URL):

   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   ```

4. Confirm the directory:

   ```bash
   ls
   ```

   You should see a folder similar to `EKS` that contains:

   - `backend/`
   - `frontend/`
   - `docker-compose.yml`
   - `k8s/`
   - `docs/`
   - `ec2_deply/` (this folder)

Make a note of the **full path** to that directory, for example:

```bash
/home/ec2-user/EKS
```

We will use that in the next steps.

---

### 3.6 Option B – Copy your local folder using `scp`

If you are working with a local folder `/home/Akshay/AWS/EKS` on your machine and don’t have a Git remote (or don’t want to use it), you can **copy the folder directly** to EC2.

From your **local machine** (not inside EC2), run:

```bash
cd /home/Akshay

scp -i ~/.ssh/bedrock-ec2-key.pem -r AWS \
  ec2-user@<EC2_PUBLIC_IP>:/home/ec2-user/
```

Explanation:

- `-i ~/.ssh/bedrock-ec2-key.pem` – uses your SSH key.
- `-r AWS` – recursively copy the `AWS` directory (which contains `EKS`).
- Destination: `/home/ec2-user/` on the EC2 instance.

After the copy finishes, SSH back into the EC2 instance and run:

```bash
ssh -i ~/.ssh/bedrock-ec2-key.pem ec2-user@<EC2_PUBLIC_IP>

cd /home/ec2-user
ls
```

You should see an `AWS` directory; inside that, the `EKS` project:

```bash
cd /home/ec2-user/AWS/EKS
ls
```

You should see:

- `backend/`
- `frontend/`
- `docker-compose.yml`
- `ec2_deply/`
- etc.

Make a note: we will assume the project lives at:

```bash
/home/ec2-user/AWS/EKS
```

Adjust if your path is different.

---

### 3.7 Quick sanity check – Docker + project present

Before we go to the actual deployment, verify:

1. Docker is running:

   ```bash
   docker ps
   ```

   It should show an empty list (no error).

2. The project directory exists:

   ```bash
   ls /home/ec2-user/AWS/EKS
   ```

   You should see `docker-compose.yml`, `backend`, `frontend`, `ec2_deply`, etc.

If both are true, move on to `04_run_app_on_ec2_with_docker_compose.md` to actually start the app on EC2.

