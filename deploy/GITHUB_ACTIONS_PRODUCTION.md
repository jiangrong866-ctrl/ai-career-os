# GitHub Actions Production Runtime

## Required repository settings

Actions permissions:

- Workflow permissions: Read and write permissions
- Allow GitHub Actions to create and approve pull requests when needed

## Secrets

Required for full production:

- `AI_CAREER_OS_GITHUB_TOKEN`
  - Fine-grained token for the target repository.
  - Permissions: Contents write, Issues write, Pull requests write.

Optional but required for live Drive sync:

- `AI_CAREER_OS_DRIVE_RCLONE_REMOTE`
  - Example: `gdrive:AI-Career-OS`
  - The runner must be able to use rclone config. For hosted runners, provide rclone config through additional secrets or use a self-hosted runner with rclone configured.

Optional:

- `AI_CAREER_OS_ALERT_WEBHOOK_URL`

## Variables

- `AI_CAREER_OS_REPOSITORY`
  - Defaults to `github.repository`.
- `AI_CAREER_OS_BASE_BRANCH`
  - Defaults to `main`.

## Runtime

The workflow runs daily at 12:30 UTC, equivalent to 20:30 Asia/Shanghai.

Manual trigger is supported by `workflow_dispatch`.

## Rollback

Every run writes through a dedicated branch:

```text
ai-career-os/YYYY-MM-DD
```

Changes are exposed through draft PRs, so rollback is closing the PR or reverting the commit.

