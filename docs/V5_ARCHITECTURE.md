# AI Career OS v5 Architecture

AI Career OS v5 upgrades the local automation from a semi-automatic runner into a recoverable unattended loop.

## Runtime Layout

- `scripts/run_v5.py`: unified pipeline entry.
- `scripts/scheduler.py`: task metadata and next-run calculation.
- `scripts/auto_git.py`: `git add`, `git commit`, and `git push origin main` with retry.
- `scripts/recovery.py`: safe module wrapper, degraded-state handling, and error logging.
- `state/state.json`: production state file.
- `logs/v5_runtime.log`: step-by-step runtime log.
- `logs/v5_error.log`: failure and retry log.
- `dashboard/dashboard.html`: static dashboard generated after each run.
- `run_v5.cmd`: Windows Task Scheduler compatible launcher.

## Pipeline Contract

Each cycle runs in this fixed order:

1. `daily_report()`
2. `learning_module()`
3. `portfolio_module()`
4. `side_business_module()`
5. dashboard render
6. state save
7. git sync to `origin/main`

Git push failure is retried three times, logged, and marks the system as `degraded` without discarding the main outputs.
