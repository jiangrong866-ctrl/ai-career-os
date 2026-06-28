# AI Career OS v2.0 Go-Live Checklist

## GitHub

- Push this repository to GitHub.
- Enable Actions write permissions.
- Add secret `AI_CAREER_OS_GITHUB_TOKEN`.
- Optional variable: `AI_CAREER_OS_REPOSITORY`; defaults to current repo.
- Optional variable: `AI_CAREER_OS_BASE_BRANCH`; defaults to `main`.

## Drive

Choose one:

- Self-hosted runner with rclone configured and `AI_CAREER_OS_DRIVE_RCLONE_REMOTE`.
- Linux server with `DRIVE_SYNC_DIR` pointing to a mounted Drive/rclone folder.

Without this, Drive sync stays in explicit queue mode.

## Remote Execution

Preferred:

- GitHub Actions cron in `.github/workflows/ai-career-os.yml`.

Fallback:

- Linux systemd service in `deploy/systemd-ai-career-os.service`.
- Docker compose in `docker-compose.yml`.
- cron fallback in `deploy/cron-ai-career-os`.

## Verification

```bash
python scripts/production_readiness.py
python scripts/healthcheck.py
python scripts/uptime_monitor.py
```

Go-live is complete only when:

- `production_autonomous_capability` is `true`
- GitHub sync state is `ok: true`
- Drive sync state is `ok: true`
- healthcheck is `ok: true`

