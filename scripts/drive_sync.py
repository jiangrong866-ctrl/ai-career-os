import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DATA = ROOT / "data"
QUEUE = ROOT / "queue" / "drive"
STATE = ROOT / "state"


def sync_drive(today: str | None = None) -> dict:
    rclone_remote = os.environ.get("DRIVE_RCLONE_REMOTE")
    drive_dir = os.environ.get("DRIVE_SYNC_DIR")
    production = os.environ.get("AI_CAREER_OS_PRODUCTION", "").lower() in {"1", "true", "yes"}
    manifest = {
        "date": today,
        "files": [
            str(REPORTS / f"daily_report_{today}.md") if today else "",
            str(DATA / "jobs" / "jd_cards.jsonl"),
            str(DATA / "side_business" / "history.jsonl"),
            str(DATA / "learning" / "growth_track.jsonl"),
        ],
    }
    if rclone_remote:
        copied = []
        for raw in manifest["files"]:
            if not raw:
                continue
            src = Path(raw)
            if src.exists():
                target = f"{rclone_remote.rstrip('/')}/"
                subprocess.run(["rclone", "copyto", str(src), target + src.name], check=True, capture_output=True, text=True)
                copied.append(target + src.name)
        result = {"ok": True, "mode": "rclone", "target": rclone_remote, "copied": copied}
        STATE.mkdir(exist_ok=True)
        (STATE / "drive_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    if not drive_dir:
        QUEUE.mkdir(parents=True, exist_ok=True)
        path = QUEUE / f"drive_sync_{today or 'latest'}.json"
        reason = "DRIVE_SYNC_DIR or DRIVE_RCLONE_REMOTE not configured"
        path.write_text(json.dumps({"ok": False, "reason": reason, **manifest}, indent=2), encoding="utf-8")
        result = {"ok": False, "reason": reason, "queue_file": str(path), "production_blocking": production}
        STATE.mkdir(exist_ok=True)
        (STATE / "drive_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        if production:
            raise RuntimeError(reason)
        return result

    target = Path(drive_dir)
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for raw in manifest["files"]:
        if not raw:
            continue
        src = Path(raw)
        if src.exists():
            dst = target / src.name
            shutil.copy2(src, dst)
            copied.append(str(dst))
    result = {"ok": True, "target": str(target), "copied": copied}
    STATE.mkdir(exist_ok=True)
    (STATE / "drive_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(sync_drive(), indent=2))
