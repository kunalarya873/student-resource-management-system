# Git Submodules & Multi-Repo Architecture Guide 🔀

This guide explains how to split the **Frontend** (for Vercel) and **Backend** (for AWS EC2) into separate GitHub repositories, while keeping them linked to this main repository as **Git Submodules**.

---

## 🏛️ Architecture & Target Repositories

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MAIN REPOSITORY (Orchestrator)                       │
│                   github.com/<username>/student-resource-system       │
│                                                                        │
│   ├── .gitmodules                                                      │
│   ├── Makefile                                                         │
│   ├── docker-compose.prod.yml                                          │
│   ├── docs/                                                            │
│   ├── backend/  ──(submodule)──► github.com/<user>/student-backend.git │
│   │                                       │ (GitHub Actions)           │
│   │                                       ▼                            │
│   │                                   [ AWS EC2 ]                      │
│   │                                                                    │
│   └── frontend/ ──(submodule)──► github.com/<user>/student-frontend.git│
│                                           │ (Instant Vercel CI/CD)     │
│                                           ▼                            │
│                                       [ Vercel ]                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Step-by-Step Migration Instructions

### Step 1: Create Two New Empty Repositories on GitHub

Go to [GitHub New Repository](https://github.com/new) and create two **empty** repositories (without README, without license):
1. `student-resource-backend`
2. `student-resource-frontend`

---

### Step 2: Initialize & Push the Backend Repository

Open your terminal in the `backend/` directory:

```bash
cd backend

# Initialize standalone git repository (if not already a git repo)
git init -b main
git add .
git commit -m "feat: initial commit of backend repository for EC2 deployment"

# Connect to your new backend GitHub repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/student-resource-backend.git

# Push to main
git push -u origin main

cd ..
```

---

### Step 3: Initialize & Push the Frontend Repository

Open your terminal in the `frontend/` directory:

```bash
cd frontend

# Initialize standalone git repository
git init -b main
git add .
git commit -m "feat: initial commit of frontend repository for Vercel deployment"

# Connect to your new frontend GitHub repository
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/student-resource-frontend.git

# Push to main
git push -u origin main

cd ..
```

---

### Step 4: Link Both as Git Submodules in the Main Repository

Once both repositories are pushed to GitHub, link them inside your main repository:

```bash
# In the root project directory:

# Remove cached directory tracking from the main repo index
git rm -r --cached backend
git rm -r --cached frontend

# Add them as submodules
git submodule add https://github.com/<YOUR_GITHUB_USERNAME>/student-resource-backend.git backend
git submodule add https://github.com/<YOUR_GITHUB_USERNAME>/student-resource-frontend.git frontend

# Commit the submodule references and .gitmodules
git add .gitmodules backend frontend
git commit -m "chore: convert backend and frontend into git submodules"
git push origin main
```

---

## 🚀 Deployment Instructions for Each Platform

### 1. Frontend on Vercel:
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New** $\rightarrow$ **Project**.
3. Select the `student-resource-frontend` repository.
4. **Settings:**
   - Framework Preset: **Vite**
   - Root Directory: `./`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Environment Variable:**
   - `VITE_API_BASE_URL`: `http://<YOUR_EC2_PUBLIC_IP>:8000/api/v1` (or your domain `https://api.yourdomain.com/api/v1`)
6. Click **Deploy**. Vercel will build and assign you a `*.vercel.app` URL.

### 2. Backend on AWS EC2 via GitHub Actions:
1. Go to your `student-resource-backend` repository on GitHub.
2. Under **Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions**, add the required secrets:
   - `EC2_HOST` (EC2 Public IP)
   - `EC2_USER` (`ubuntu`)
   - `EC2_SSH_KEY` (Your `.pem` private key)
   - `DATABASE_URL` (Supabase Postgres URI)
   - `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE`
   - `JWT_SECRET_KEY`
   - `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
   - `FRONTEND_URL` (Set to your Vercel URL, e.g. `https://student-resource-frontend.vercel.app`)
3. The workflow in `.github/workflows/deploy.yml` automatically triggers on push to `main`!

---

## 🔄 Daily Workflow with Submodules

When you or another team member clones the main repository:

```bash
# Clone with all submodules in one command:
git clone --recurse-submodules https://github.com/<YOUR_USERNAME>/student-resource-system.git

# Or if cloned normally:
git submodule update --init --recursive

# Pull latest changes across all submodules:
git submodule update --remote --merge
```
