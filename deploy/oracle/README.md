# Deploy backend on Oracle Cloud (free tier)

Host the FastAPI + ML backend on Oracle's **Always Free** ARM VM, then connect your Vercel frontend over HTTPS.

## Why Cloudflare Tunnel?

Your Vercel site is **HTTPS**. Browsers block API calls to plain `http://` (mixed content). The tunnel gives a free **https://** URL without buying a domain.

---

## Step 1 — Create Oracle Cloud VM

1. Sign up at [cloud.oracle.com](https://cloud.oracle.com) (Always Free tier).
2. **Compute → Instances → Create instance**
3. Settings:
   - **Name:** `rag-backend`
   - **Image:** Ubuntu 22.04 or 24.04 (**Always Free eligible**, ARM)
   - **Shape:** `VM.Standard.A1.Flex` → **2 OCPU**, **12 GB RAM**
   - **Boot volume:** 50 GB (default)
   - **Networking:** assign a **public IPv4**
   - **SSH keys:** add your public key (generate with `ssh-keygen -t ed25519` if needed)
4. Click **Create**.

### Open port 8000 (optional; tunnel works without public 8000)

**Networking → Virtual cloud networks → your VCN → Security Lists → Default**

Add **Ingress Rule**:

| Source | Protocol | Port |
|--------|----------|------|
| `0.0.0.0/0` | TCP | `8000` |

Also on the VM:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 2 — SSH into the VM

```bash
ssh ubuntu@YOUR_VM_PUBLIC_IP
```

(Use `opc@...` if you picked Oracle Linux instead of Ubuntu.)

---

## Step 3 — Clone repo and configure

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/akg78/Single-Document-RAG-Assistant.git
cd Single-Document-RAG-Assistant

cp deploy/oracle/.env.example deploy/oracle/.env
nano deploy/oracle/.env   # set OPENAI_API_KEY
```

---

## Step 4 — Install Docker and start backend

```bash
bash deploy/oracle/setup.sh
```

First Docker build can take **20–40 minutes** (PyTorch + models).

Verify:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

---

## Step 5 — HTTPS tunnel (for Vercel)

```bash
bash deploy/oracle/tunnel.sh
```

Copy the URL like `https://something-random.trycloudflare.com`.

Update CORS in `deploy/oracle/.env`:

```
CORS_ORIGINS=https://single-document-rag-assistant.vercel.app,https://something-random.trycloudflare.com
```

Restart backend:

```bash
docker compose -f deploy/oracle/docker-compose.yml up -d
```

> **Note:** Quick tunnel URLs change each restart. For a stable URL, use a [named Cloudflare tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) with a free domain.

---

## Step 6 — Connect Vercel frontend

1. [Vercel → Environment Variables](https://vercel.com/akg78s-projects/single-document-rag-assistant/settings/environment-variables)
2. Set `NEXT_PUBLIC_API_URL` = your **https** tunnel URL (no trailing slash)
3. Redeploy the frontend

---

## Useful commands

```bash
# Logs
docker compose -f deploy/oracle/docker-compose.yml logs -f

# Restart
docker compose -f deploy/oracle/docker-compose.yml restart

# Stop
docker compose -f deploy/oracle/docker-compose.yml down

# Free disk space
docker system prune -af
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Out of memory during build | Ensure VM has **12 GB RAM**; close other containers |
| Build fails on ARM | Images use `linux/arm64`; rebuild with `--no-cache` |
| Vercel can't reach API | Use **HTTPS** tunnel URL, not `http://IP:8000` |
| CORS error | Add Vercel + tunnel URLs to `CORS_ORIGINS` |
| Disk full | `docker system prune -af` (boot volume is only ~50 GB) |
