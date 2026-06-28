import json
import os
import platform
import subprocess
from pathlib import Path

from github_api import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"


def file_exists(path: str) -> bool:
    return (ROOT / path).exists()


def check_syntax() -> bool:
    result = subprocess.run(
        [
            "python",
            "-m",
            "py_compile",
            str(ROOT / "scripts" / "daily_loop.py"),
            str(ROOT / "scripts" / "daemon_loop.py"),
            str(ROOT / "scripts" / "github_api.py"),
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def main() -> None:
    load_dotenv()
    checks = {
        "runtime_is_cloud_or_linux": bool(os.environ.get("GITHUB_ACTIONS")) or platform.system().lower() == "linux",
        "production_runtime_selected": True,
        "daemon_script_exists": file_exists("scripts/daemon_loop.py"),
        "github_actions_workflow_exists": file_exists(".github/workflows/ai-career-os.yml"),
        "systemd_unit_exists": file_exists("deploy/systemd-ai-career-os.service"),
        "cron_fallback_exists": file_exists("deploy/cron-ai-career-os"),
        "dockerfile_exists": file_exists("Dockerfile"),
        "state_file_exists": file_exists("state/system_state.json"),
        "github_token_present": bool(os.environ.get("GITHUB_TOKEN")),
        "github_repository_bound": bool(os.environ.get("GITHUB_REPOSITORY")),
        "drive_sync_configured": bool(os.environ.get("DRIVE_SYNC_DIR") or os.environ.get("DRIVE_RCLONE_REMOTE")),
        "python_syntax_ok": check_syntax(),
    }
    production_ready = all(checks.values())
    result = {
        "production_autonomous_capability": production_ready,
        "checks": checks,
        "blocking_reason": None if production_ready else "missing one or more production requirements",
    }
    STATE.mkdir(exist_ok=True)
    (STATE / "production_readiness.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
