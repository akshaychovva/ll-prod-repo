# 3. Create the GitHub repository

Create an empty repository on GitHub that will hold your code.

---

## 3.1 Prerequisites

- A **GitHub account** (free at [github.com](https://github.com)).
- A name for your repo (e.g. `bedrock-llm-demo`, `llm-app`, `EKS`).

---

## 3.2 Steps (GitHub website)

1. Log in to GitHub.
2. Click the **+** (top right) → **New repository**.
3. Fill in:
   - **Repository name**: e.g. `bedrock-llm-demo` (or whatever you prefer).
   - **Description** (optional): e.g. `Streamlit + Flask + Postgres + Bedrock LLM demo`.
   - **Visibility**: Public or Private (your choice).
4. **Important**: Do **not** check:
   - ❌ Add a README file  
   - ❌ Add .gitignore  
   - ❌ Choose a license  

   You already have these locally. An empty repo is what we want.
5. Click **Create repository**.

---

## 3.3 Note the repository URL

After creation, GitHub shows you the repo URL. It will look like:

- **HTTPS**: `https://github.com/<your-username>/<repo-name>.git`
- **SSH**: `git@github.com:<your-username>/<repo-name>.git`

Example: `https://github.com/akshay/bedrock-llm-demo.git`

You will use this in the next step when adding the remote and pushing.

---

## 3.4 Default branch name

GitHub’s default branch is usually `main`. If your local branch is `main`, you’re aligned. If you use `master`, you can either:

- Rename: `git branch -M main`, or  
- Push to `master` and change the default branch in GitHub settings later.

For simplicity, we’ll assume `main` in the next file.

---

## 3.5 Summary

- Create an **empty** repo (no README, no .gitignore, no license).
- Copy the repo URL for the next step.

Next: `04_push_from_local.md` to push your local code to GitHub.
