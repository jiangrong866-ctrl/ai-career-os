# Production Autonomous System v1.2

## Definition

AI Career OS v1.2 is production-capable when it runs on Linux/cloud with:

- systemd or Docker restart policy
- persistent state volume
- GitHub token and repository binding
- Drive sync directory or service integration
- structured input queue or API/MCP input source

## Cycle Contract

Each cycle must complete:

1. Input collected
2. Analysis completed
3. Decision generated
4. Execution performed
5. Local state persisted
6. GitHub updated or queued with explicit reason
7. Drive updated or queued with explicit reason
8. State saved and healthcheck passing

## Runtime Roles

- Windows: dev/fallback runtime
- Linux/cloud server: production runtime

## Blocking Conditions

The system is not production autonomous when any of these are missing:

- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`
- `DRIVE_SYNC_DIR` or equivalent Drive service integration
- Linux/systemd/Docker supervisor

## Verification Commands

```bash
python scripts/production_readiness.py
python scripts/healthcheck.py
python scripts/github_api.py
python scripts/drive_sync.py
```

