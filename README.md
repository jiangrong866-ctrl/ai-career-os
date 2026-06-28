# AI Career Operating System

This workspace defines the MVP automation loop for:

- AI career transition in Chongqing
- Side-business content and service production
- Portfolio improvement and publishing

The operating model is:

```text
input -> analysis -> decision -> execution -> output
```

Primary tools:

- Chrome: read-only collection from logged-in web pages
- Google Drive: knowledge base and reusable assets
- Google Sheets: task state and daily ledger
- Google Calendar: daily scheduling and reminders
- GitHub: portfolio code and project delivery
- Gmail: HR and collaboration communication

Daily runtime:

- Time: 20:30-21:00 Asia/Shanghai
- Calendar event: AI Career OS Daily Loop
- Windows scheduled task: AI Career OS Daily Loop
- Scope: 1 job scan, 1 learning task, 1 side-business output, 1 portfolio improvement

Autonomous loop v2.0:

- Production runtime: GitHub Actions or Linux/cloud server.
- Dev/fallback runtime: Windows.
- Trigger: `scripts/daemon_loop.py` is the primary daemon loop.
- Fallback trigger: Windows Task Scheduler can run `scripts/run_daily_loop.cmd`.
- Decision: weighted scoring selects Top 3 jobs and the best side-business task.
- State: `state/system_state.json` records stage, failures, retries, pending tasks, and verification.
- Persistence: local CSV/JSONL/Markdown files, Drive sync or queue, and GitHub API or queue.
- Enforcement: every run must produce a concrete file and update at least one persistence layer.
- Safety: emails, job applications, public publishing, and third-party website writes require explicit confirmation.

Hard autonomous mode:

```powershell
python scripts\daemon_loop.py
```

Server mode:

- Use `deploy/systemd-ai-career-os.service`.
- Set `GITHUB_TOKEN` and `GITHUB_REPOSITORY` to enable real GitHub API writes.
- Set `DRIVE_SYNC_DIR` to a mounted Drive/rclone folder to enable production Drive sync.
- Put structured job inputs in `queue/structured_input/`; Chrome is manual fallback only.

GitHub Actions cloud runtime:

- Workflow: `.github/workflows/ai-career-os.yml`
- Schedule: daily 12:30 UTC / 20:30 Asia-Shanghai
- Required secret: `AI_CAREER_OS_GITHUB_TOKEN`
- Optional live Drive sync: `AI_CAREER_OS_DRIVE_RCLONE_REMOTE`
- Optional alerting: `AI_CAREER_OS_ALERT_WEBHOOK_URL`

Production readiness:

```powershell
python scripts\production_readiness.py
python scripts\healthcheck.py
```
