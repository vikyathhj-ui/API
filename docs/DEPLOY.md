# Going live: deploy to a server (step by step)

**Time:** about 1–2 hours the first time. **Cost:** a small server (about €6–10/month) plus a domain (about $10–15/year).
Everything below is typed into a terminal. Lines in grey boxes are commands: copy them one at a time.

> **Decisions only you can make:** which hosting provider, which domain name, and whether to go live.
> Nothing here happens automatically. You are in control of every step.

## What you are building
```
 internet ──HTTPS──▶ Caddy (ports 80/443, automatic certificates)
                         │
                         ▼
                    API (FastAPI) ──▶ Validator (KoSIT)    all on one server,
                         │       ──▶ PostgreSQL (data)    in Docker containers,
                         │       ──▶ Redis (rate limits)  not reachable from outside
```

## 1. Rent a server
Any provider with a Linux virtual machine works. A common low-cost choice is **Hetzner Cloud** (EU data centres, good for EU customers' privacy expectations).
- Size: **2 vCPU, 4 GB RAM** is plenty to start (measured: ~11 invoices/second on 4 cores; the stack uses about 700 MB of RAM).
- Operating system: **Ubuntu 24.04**.
- Add your **SSH key** when creating it (the provider explains how), so you log in without a password.

Write down the server's **IP address**.

## 2. Point your domain at it
At your domain registrar, add a DNS record: type **A**, name `api` (or whatever you like), value = the server's IP.
Your API will live at `https://api.yourdomain.com`. DNS changes can take a few minutes to an hour.

## 3. Log in and install Docker
From your computer:

```bash
ssh root@YOUR_SERVER_IP
```

On the server, install Docker using Docker's official script:

```bash
curl -fsSL https://get.docker.com | sh
```

Then switch on a basic firewall that allows only SSH and web traffic:

```bash
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp && ufw --force enable
```

## 4. Get the code onto the server

```bash
git clone https://github.com/vikyathhj-ui/API.git /opt/invoiceformat
```

```bash
cd /opt/invoiceformat
```

(If the repository is private, GitHub will ask you to log in. A "deploy key" or personal access token works.)

## 5. Configure

```bash
cp .env.example .env
```

Create a strong database password and put it into `.env`:

```bash
sed -i "s#^POSTGRES_PASSWORD=.*#POSTGRES_PASSWORD=$(openssl rand -base64 30 | tr -d '/+=')#" .env
```

Then edit the rest (`nano .env`; save with Ctrl+O, Enter, then exit with Ctrl+X):
- `DOMAIN=api.yourdomain.com`
- `CONTACT_EMAIL=` your support email (shown on the website)
- `PRODUCT_NAME=` your product's name
- Optional: `PAYMENT_LINK_STARTER=`, `PAYMENT_LINK_GROWTH=`, `PAYMENT_LINK_SCALE=` (see [SELLING.md](SELLING.md))

## 6. Build and start

```bash
bash scripts/build-images.sh
```

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

Caddy now requests a free HTTPS certificate. Check that everything is healthy:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml ps
```

```bash
curl https://api.yourdomain.com/v1/health
```

You should see `{"status":"ok",...}`. Open `https://api.yourdomain.com` in your browser to see the website.

## 7. Prove it works end to end
Create a key for yourself and run the full check (it generates real invoices and validates them with veraPDF and Mustang):

```bash
docker compose exec api python -m app.admin create --email you@yourdomain.com --plan scale
```

```bash
API_KEY=<the key printed above> BASE_URL=https://api.yourdomain.com bash scripts/e2e-check.sh
```

## 8. Backups (do not skip)
Run a daily database backup at 03:17 UTC:

```bash
(crontab -l 2>/dev/null; echo '17 3 * * * cd /opt/invoiceformat && bash deploy/backup.sh >> backups/backup.log 2>&1') | crontab -
```

Copy the `backups/` folder off the server regularly (e.g. to a storage box or your computer with `scp`). Test a restore now and then (see [OPERATIONS.md](OPERATIONS.md)).

## 9. Monitoring (free)
Create a free uptime monitor (e.g. UptimeRobot or Better Stack) that checks `https://api.yourdomain.com/v1/health` every 5 minutes and emails you when it fails.

## Updating to a new version

```bash
cd /opt/invoiceformat && git pull && bash scripts/build-images.sh
```

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d
```

Your data (database volume) and certificates (Caddy volume) are kept. Take a backup before every update.

## Difference between local and production
| | Local (`docker compose up`) | Production (+ `deploy/docker-compose.prod.yml`) |
|---|---|---|
| Who can reach it | only your computer (127.0.0.1:8000) | the internet, via HTTPS on your domain |
| HTTPS | no | yes, automatic (Let's Encrypt) |
| API port | published on 127.0.0.1 | not published; only Caddy can reach it |
