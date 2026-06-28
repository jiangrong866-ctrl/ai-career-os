# Hard Autonomous System v1.1

## Trigger

Primary trigger is `scripts/daemon_loop.py`.

The Windows scheduled task is now a fallback launcher, not the only daily trigger.

## State Machine

Persistent state lives in `state/system_state.json` and records:

- `last_run_time`
- `current_stage`
- `failure_count`
- `retry_queue`
- `pending_tasks`
- `last_successful_run`
- `last_verification`

## Input Policy

Chrome is not a primary data source.

Input priority:

1. API
2. MCP
3. Structured input queue under `queue/structured_input/`
4. Manual import
5. Chrome manual fallback

## GitHub API

`scripts/github_api.py` syncs queued file updates to GitHub when these environment variables exist:

- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`
- `GITHUB_BASE_BRANCH` optional, default `main`

The adapter supports file update, issue creation, and draft PR creation.

## Recovery

Any failed stage writes to:

- `logs/error.log`
- `queue/retry/retry_queue.jsonl`
- `state/system_state.json`

The next daemon cycle keeps running and retries from structured persisted inputs.

