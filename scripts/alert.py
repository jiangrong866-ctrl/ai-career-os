import json
import os
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
LOGS = ROOT / "logs"


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def send_webhook(payload: dict) -> dict:
    url = os.environ.get("ALERT_WEBHOOK_URL")
    if not url:
        return {"ok": False, "reason": "ALERT_WEBHOOK_URL not configured"}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return {"ok": 200 <= response.status < 300, "status": response.status}


def main() -> None:
    state = read_json(STATE / "system_state.json", {})
    readiness = read_json(STATE / "production_readiness.json", {})
    payload = {
        "system": "AI Career OS",
        "state": state,
        "readiness": readiness,
    }
    result = send_webhook(payload)
    LOGS.mkdir(exist_ok=True)
    (LOGS / "last_alert.json").write_text(json.dumps({"payload": payload, "result": result}, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

