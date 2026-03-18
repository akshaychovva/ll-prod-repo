# 4. Push from local to GitHub

This is the actual push. Run these commands from your project root.

---

## 4.1 Open a terminal in your project

```bash
cd /home/Akshay/AWS/EKS
```

---

## 4.2 Check if Git is already initialized

```bash
git status
```

- If you see "not a git repository": run `git init`.
- If you see branch names and file status: Git is already set up, skip to 4.4.

---

## 4.3 Initialize Git (only if needed)

```bash
git init
git branch -M main
```

---

## 4.4 Add files and commit

```bash
# Add everything (respecting .gitignore)
git add .

# See what will be committed
git status

# Commit
git commit -m "Initial commit: backend, frontend, docker-compose, deploy docs"
```

**Before committing**, check `git status` output. You should **not** see:

- `.env`
- `venv/`
- `*.pem`
- `.ssh/`

If you do, fix `.gitignore` and run `git reset` then `git add .` again.

---

## 4.5 Add the GitHub remote

Replace `<your-username>` and `<repo-name>` with your actual values:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
```

Example:

```bash
git remote add origin https://github.com/akshay/bedrock-llm-demo.git
```

If you already have a remote named `origin` (e.g. from an earlier setup):

```bash
git remote -v
git remote set-url origin https://github.com/<your-username>/<repo-name>.git
```

---

## 4.6 Push to GitHub

```bash
git push -u origin main
```

- First push may ask for GitHub credentials (username + password or token).
- If you use **2FA**, use a **Personal Access Token** instead of your password.
- To create a token: GitHub → Settings → Developer settings → Personal access tokens.

---

## 4.7 If you have existing branches (e.g. akshay_dev)

Your repo might have `akshay_dev` as well as `main`. To push the current branch:

```bash
git push -u origin main
```

To push another branch:

```bash
git checkout akshay_dev
git push -u origin akshay_dev
```

For CI/CD (e.g. GitHub Actions), you’ll usually trigger on `main`.

---

## 4.8 Summary

- `git add .` (respects .gitignore)
- `git commit -m "..."`
- `git remote add origin <url>`
- `git push -u origin main`

Next: `05_verify_and_next_steps.md` to confirm everything works and connect to CI/CD.
