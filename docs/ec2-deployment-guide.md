# AWS EC2 Deployment Guide & GitHub Actions CI/CD 🚀

This guide provides step-by-step instructions to configure an AWS EC2 instance and connect it with GitHub Actions for automated continuous integration and continuous deployment (CI/CD).

---

## 🏗️ Architecture Overview

```
                      GitHub Repository (Push / PR to main)
                                     │
                                     ▼
                      GitHub Actions: Stage 1 (CI)
                      ├── Ruff Lint & Format Check
                      └── Pytest Automated Test Suite (88 tests)
                                     │
                                     ▼ (Only on push to main)
                      GitHub Actions: Stage 2 (CD)
                      ├── Connects via SSH (`appleboy/ssh-action`)
                      ├── Syncs latest code
                      ├── Runs Alembic database migrations (Supabase)
                      ├── Builds & recreates backend container (`docker compose`)
                      └── Smoke test healthcheck verification (`/healthz`)
                                     │
                                     ▼
                         AWS EC2 Production Server
                         [ Docker Container: Port 8000 ]
```

---

## 📋 Step 1: AWS EC2 Instance Setup

1. **Launch EC2 Instance:**
   - **OS:** Ubuntu Server 22.04 LTS or 24.04 LTS (HVM), SSD Volume Type
   - **Instance Type:** `t3.small` or `t3.medium` (recommended: at least 2 GB RAM for Docker builds)
   - **Storage:** 20 GB gp3 SSD
   - **Key Pair:** Create or select an existing key pair (e.g. `amu-backend-key.pem`) and download it.

2. **Configure Security Group Inbound Rules:**

   | Type | Protocol | Port Range | Source | Purpose |
   | :--- | :---: | :---: | :--- | :--- |
   | **SSH** | TCP | `22` | `0.0.0.0/0` (or your IP) | Remote administrative access & GitHub Actions SSH |
   | **Custom TCP** | TCP | `8000` | `0.0.0.0/0` | Direct backend API access |
   | **HTTP** | TCP | `80` | `0.0.0.0/0` | Standard HTTP (for optional Nginx reverse proxy) |
   | **HTTPS** | TCP | `443` | `0.0.0.0/0` | Standard HTTPS (for SSL/TLS) |

---

## ⚙️ Step 2: Provision the EC2 Instance (One-Time Setup)

Connect to your EC2 instance via SSH:
```bash
chmod 400 amu-backend-key.pem
ssh -i amu-backend-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

Execute the automated provisioning script:
```bash
# Clone the repository onto the server (or download the setup script)
mkdir -p ~/app
cd ~/app
git clone https://github.com/<YOUR-GITHUB-ORG-OR-USER>/<YOUR-REPO-NAME>.git .

# Run the setup script to install Docker, Docker Compose, Git, and UFW firewall
chmod +x deploy/ec2-setup.sh
./deploy/ec2-setup.sh

# Apply docker group changes without logging out
newgrp docker
```

---

## 🔑 Step 3: Configure GitHub Repository Secrets

In your GitHub repository, navigate to:
**Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions $\rightarrow$ New repository secret**

Add the following required secrets:

### EC2 Connection Secrets:
| Secret Name | Value Example | Description |
| :--- | :--- | :--- |
| `EC2_HOST` | `54.254.120.45` | Public IPv4 address or Elastic IP of your EC2 instance |
| `EC2_USER` | `ubuntu` | Default username for Ubuntu instances |
| `EC2_SSH_KEY` | `-----BEGIN RSA PRIVATE KEY-----\nMIIE...` | The entire contents of your `.pem` private key file |
| `EC2_SSH_PORT` | `22` | SSH port (defaults to 22) |

### Application & Database Secrets:
| Secret Name | Value Example | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://postgres.ijlfghksvuyoynshxoif:ChaiPani%401234@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?ssl=require` | Supabase Postgres Pooler connection URI |
| `JWT_SECRET_KEY` | `your-cryptographic-jwt-secret-min-32-chars` | Key used for signing JWT access and refresh tokens |
| `SUPABASE_URL` | `https://ijlfghksvuyoynshxoif.supabase.co` | Supabase project API URL |
| `SUPABASE_KEY` | `eyJhbGciOi...` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE` | `eyJhbGciOi...` | Supabase service role key (for administrative storage) |
| `SUPABASE_BUCKET` | `resources` | Supabase Storage bucket name |
| `SUPABASE_REGION` | `ap-southeast-2` | Supabase project region |
| `SUPABASE_WEBHOOK_SECRET`| `whsec_supabase_storage_secure_2026` | Webhook verification secret |
| `EMAIL_HOST_USER` | `your-email@gmail.com` | SMTP username for OTP and sharing emails |
| `EMAIL_HOST_PASSWORD` | `your-google-app-password` | SMTP App password |
| `FRONTEND_URL` | `http://<FRONTEND_IP_OR_DOMAIN>` | Allowed frontend CORS URL |

---

## 🚢 Step 4: Triggering Deployments

Deployments occur automatically:
1. **Push to `main` branch:** Any commit pushed or PR merged to `main` triggers the pipeline.
2. **Quality Gate:** Stage 1 (`ci`) runs linting, formatting checks, and the 88-test pytest suite.
3. **Deployment Gate:** If Stage 1 passes, Stage 2 (`deploy`) connects to EC2 via SSH, executes Alembic migrations, rebuilds the Docker container, and verifies health via `/healthz`.
4. **Manual Trigger:** You can also trigger a deployment on-demand from the **Actions** tab in GitHub by selecting **Backend CI/CD Pipeline $\rightarrow$ Run workflow**.

---

## 🔍 Step 5: Monitoring & Troubleshooting

To monitor the running container directly on your EC2 instance:

```bash
# Check running containers
docker ps

# View backend application logs in real-time
docker logs -f amu_backend_prod

# Inspect health check status
curl -i http://localhost:8000/healthz

# Restart container manually if needed
cd ~/app
docker compose -f docker-compose.prod.yml restart backend
```
