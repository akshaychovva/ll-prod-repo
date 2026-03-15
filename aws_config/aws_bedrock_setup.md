### AWS CLI and Amazon Bedrock setup (for this app)

This file explains:

- How to run `aws configure` for the AWS CLI.
- How to enable and configure **Amazon Bedrock** (with Anthropic models) for use from code.
- What the **Anthropic “org name / URL”** questions mean.
- Whether you should use the **Amazon Bedrock playground** and how free/credits work at a high level.

This is written for a **personal / free‑tier account** where you are just learning.

---

### 1. Configure the AWS CLI (`aws configure`)

The backend in this app uses the standard AWS SDK credential chain. The simplest way to get working credentials on your machine (and on EC2 if you use profiles) is to configure the AWS CLI.

#### 1.1 Install the AWS CLI (if not already installed)

- On Linux:

  ```bash
  # Example for many distros – check AWS docs if this fails
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install
  aws --version
  ```

If `aws --version` prints a version, the CLI is installed.

#### 1.2 Run `aws configure`

In a terminal on your local machine:

```bash
aws configure
```

You will be asked 4 questions:

1. **AWS Access Key ID**  
   - This comes from the AWS console:  
     - Go to `IAM → Users → <your-user> → Security credentials → Create access key`.  
   - Copy/paste the Access Key ID.

2. **AWS Secret Access Key**  
   - Copy/paste the Secret Access Key shown once when you create the key.  
   - **Keep this secret** – do not commit it to Git.

3. **Default region name**  
   - Use the same region where you enable Bedrock, e.g.:
     - `us-east-1` (N. Virginia) or
     - `us-west-2` (Oregon), etc.

4. **Default output format**  
   - You can enter `json` or just press Enter for the default.

This writes to:

- `~/.aws/credentials`
- `~/.aws/config`

#### 1.3 Verify your identity and region

Run:

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and user/role ARN.

Run:

```bash
aws configure get region
```

This should print the region you set (e.g. `us-east-1`).  
This **must match** the region where you enable **Amazon Bedrock** for the app to work.

---

### 2. Enable Amazon Bedrock and request model access

Amazon Bedrock is **not always enabled by default**. You must:

1. Turn on the service (if needed).
2. Request access to specific **foundation models** (e.g. Anthropic Claude).

#### 2.1 Open the Bedrock console

1. Log in to the AWS console.
2. Make sure you are in your chosen **region** (top‑right).
3. In the search bar, type **“Bedrock”** and open **Amazon Bedrock**.

If it’s your first time:

- You may see a “Get started” or “Enable” screen.
- Follow the prompts to enable the service in your account.

#### 2.2 Request access to models (including Anthropic)

Within the Bedrock console:

1. Go to **“Model access”** (or similar menu, depends on UI version).
2. You’ll see a list of providers and models, e.g.:
   - Amazon (Titan)
   - **Anthropic** (Claude family)
   - Others (AI21, Cohere, etc.).
3. For the models you want to use (for this app, often **Anthropic Claude** models):
   - Check the boxes.
   - Click **“Request access”** or **“Save changes”**.

Sometimes, for certain providers (e.g. Anthropic via Bedrock), AWS asks for:

- **Organization name**
- **Website / URL**

You can:

- Use your own full name as **organization name** if you are an individual.
- Use any personal or GitHub page URL, or even `https://example.com` if you do not have a site.  
  This is mainly for AWS/Anthropic to have some context on who is using the models.

After submitting:

- Access may be **granted immediately** or may take some time, depending on model and region.

---

### 3. Using Bedrock from the CLI (to test that access works)

Once you believe you have access, you can test via CLI.

#### 3.1 List available foundation models

Run:

```bash
aws bedrock list-foundation-models --region <your-region>
```

Replace `<your-region>` with the region you configured (e.g. `us-east-1`).

If Bedrock is enabled and you have permissions, you should see a JSON list of models.  
Look for Anthropic models in the output (names like `anthropic.claude-*`).

If you get **AccessDeniedException** or similar:

- Make sure:
  - Bedrock is enabled in that region.
  - Your IAM user/role has Bedrock permissions (e.g. `bedrock:ListFoundationModels`, `bedrock:InvokeModel`, etc.).

---

### 4. Anthropic “org name / URL” vs direct Anthropic accounts

You mentioned: **“Anthropic is asking org name and URL also”**.

Important distinction:

- **Option A – Use Anthropic through Amazon Bedrock (what this app expects)**:
  - You stay **inside AWS**.
  - You only need AWS account + Bedrock model access.
  - Anthropic fields inside the Bedrock model access form are mostly informational.
  - Billing and quotas go through AWS.

- **Option B – Use Anthropic directly (anthropic.com, their own API key)**:
  - You create a **separate Anthropic account**.
  - They may ask for organization name and website during sign‑up.
  - You get Anthropic API keys and use **their** SDK endpoints (not Bedrock’s).
  - This is **not** what the current Bedrock‑based backend uses.

For this project, you should stick with **Option A (Anthropic via Amazon Bedrock)**.  
So when AWS’s Bedrock UI asks for “org name / URL” for Anthropic models:

- Fill it with your **personal‑level** info:
  - Example:  
    - Organization: `Akshay (Personal)`  
    - URL: `https://github.com/<your-github-username>` or any URL you own/choose.

This lets AWS and Anthropic know roughly who is trying the models; it is not a strict corporate requirement for learning.

---

### 5. Bedrock playground and “Use a foundation model” (and free credits)

In the Bedrock console you will see the **Playground** and buttons like **“Use a foundation model in the Amazon Bedrock playground”**.

#### 5.1 What the playground is for

- The **Bedrock playground** lets you:
  - Experiment with prompts in the browser.
  - Try different models (e.g. Anthropic Claude, Amazon Titan).
  - Adjust temperature, max tokens, etc.
  - See responses without writing any code.

It’s useful to:

- Test your prompts.
- Confirm that the model access works.
- Get a feel for how the model behaves **before** wiring it into your code.

#### 5.2 Do we “need” the playground for this app?

- **No, it’s not required.** The app uses the **Bedrock API** directly from code.
- But using the playground is **helpful for debugging and learning**:
  - If your app fails, you can test the same prompt in the playground.
  - If it works there but fails in your app, the issue is likely credentials, IAM, or code.

So:

- You **can** click “Use a foundation model in the Amazon Bedrock playground” to play and verify everything.
- But for running the app, the important part is:
  - **Model access is granted**, and
  - Your **AWS credentials + IAM permissions** allow the app to call `bedrock:InvokeModel`.

#### 5.3 Free account and credits (high‑level only)

Details change over time, but generally:

- A **new AWS account** may get some **promotional/introductory credits** for Bedrock.
- The Bedrock console or docs may mention e.g. **$20** of credit for the playground or API usage.
- These credits:
  - Are limited in time and amount.
  - Apply to API calls (including ones made from your app), not just playground usage.

For a **learning / demo** app like this, you will usually:

- Stay well within those small free/promotional amounts if:
  - You don’t send huge prompts.
  - You don’t run massive loads or loops of calls.

But still:

- Always watch the **Billing → Cost Explorer** in AWS to be safe.

---

### 6. Minimal checklist for this project

To make the app work with Bedrock from your laptop or EC2:

1. **AWS CLI configured**
   - `aws configure` done.
   - `aws sts get-caller-identity` works.

2. **Region**
   - Same region in:
     - `aws configure` default region,
     - Bedrock console,
     - Your app’s configuration/ENV (e.g. `AWS_REGION`).

3. **Bedrock enabled and model access granted**
   - In the Bedrock console, you can:
     - Open the Playground.
     - See Anthropic models listed in `list-foundation-models`.

4. **IAM permissions**
   - Your IAM user/role has:
     - `bedrock:ListFoundationModels`
     - `bedrock:InvokeModel`
     - `bedrock:InvokeModelWithResponseStream` (if streaming).

5. **Optional: Playground sanity check**
   - Call the chosen model in the playground with a simple prompt.
   - If it works, Bedrock is enabled and model access is correct.

After this checklist, your backend code should be able to call Bedrock successfully, whether running:

- Locally via Docker Compose (see `local_deply/`), or
- On a single EC2 instance (see `ec2_deply/`), or
- Later, on EKS.

