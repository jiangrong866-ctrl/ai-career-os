# AI Career OS v1.2 Production Deployment

## Runtime Policy

- Windows is dev/fallback only.
- Linux or cloud server is the production runtime.
- systemd is preferred.
- cron is fallback.
- Docker is optional when a server supports containers.

## Required Secrets

Create `/opt/ai-career-os/.env`:

```bash
GITHUB_TOKEN=...
GITHUB_REPOSITORY=owner/repo
GITHUB_BASE_BRANCH=main
DRIVE_SYNC_DIR=/mnt/drive/AI-Career-OS
```

`GITHUB_TOKEN` should be fine-grained and limited to the target repository with:

- Contents read/write
- Issues read/write
- Pull requests read/write

## systemd

```bash
sudo cp deploy/systemd-ai-career-os.service /etc/systemd/system/ai-career-os.service
sudo systemctl daemon-reload
sudo systemctl enable --now ai-career-os
sudo systemctl status ai-career-os
```

## cron fallback

```bash
crontab deploy/cron-ai-career-os
```

## Docker

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

## Readiness

```bash
python scripts/production_readiness.py
python scripts/healthcheck.py
```

Production is not ready until both commands pass and GitHub/Drive sync states are `ok: true`.

