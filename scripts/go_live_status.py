import json
import os
from pathlib import Path

from github_api import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


load_dotenv()
system_state = read_json(STATE / "system_state.json", {})
github_sync = read_json(STATE / "github_sync.json", {})
drive_sync = read_json(STATE / "drive_sync.json", {})
readiness = read_json(STATE / "production_readiness.json", {})

token = os.environ.get("GITHUB_TOKEN") or os.environ.get("AI_CAREER_OS_GITHUB_TOKEN") or ""
repo = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("AI_CAREER_OS_REPOSITORY") or ""
token_is_placeholder = token.strip() in {"your-token", "your_github_token", "你的真实 fine-grained token"} or "fine-grained token" in token
repo_is_placeholder = repo.strip() in {"owner/repo", "username/repo-name"} or (bool(repo) and "/" not in repo)
github_ok = bool(github_sync.get("ok")) and bool(token) and bool(repo) and not token_is_placeholder and not repo_is_placeholder
drive_ok = bool(drive_sync.get("ok")) and bool(os.environ.get("DRIVE_SYNC_DIR") or os.environ.get("DRIVE_RCLONE_REMOTE"))
runtime_ok = bool(os.environ.get("GITHUB_ACTIONS")) or os.environ.get("AI_CAREER_OS_RUNTIME") == "github_actions"
loop_ok = system_state.get("current_stage") == "idle" and bool(system_state.get("last_verification", {}).get("ok"))

status = {
    "github_fully_operational": github_ok,
    "drive_production_sync": drive_ok,
    "production_runtime": "github_actions",
    "production_runtime_true": runtime_ok,
    "execution_loop_closed": loop_ok,
    "production_readiness": readiness.get("production_autonomous_capability", False),
    "go_live": github_ok and drive_ok and runtime_ok and loop_ok,
    "blocking": [],
}

if not github_ok:
    if token_is_placeholder:
        status["blocking"].append("GitHub token is still placeholder text")
    if repo_is_placeholder:
        status["blocking"].append("GitHub repository is still placeholder text")
    status["blocking"].append("GitHub token/repository/sync not verified")
if not drive_ok:
    status["blocking"].append("Drive live sync not verified")
if not runtime_ok:
    status["blocking"].append("GitHub Actions runtime not active in this environment")
if not loop_ok:
    status["blocking"].append("Execution loop verification missing or failed")

(STATE / "go_live_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
print(json.dumps(status, indent=2))
raise SystemExit(0 if status["go_live"] else 1)
