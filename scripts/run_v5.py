import datetime as dt
import html
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from auto_git import git_sync
from recovery import load_json, mark_degraded, now_iso, safe_module, save_json, write_error
from scheduler import task_summary


SCRIPTS_DIR = Path(__file__).parent
ROOT_DIR = SCRIPTS_DIR.parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
STATE_DIR = ROOT_DIR / "state"
LOG_DIR = ROOT_DIR / "logs"
DASHBOARD_DIR = ROOT_DIR / "dashboard"

STATE_PATH = STATE_DIR / "state.json"
ROOT_STATE_PATH = ROOT_DIR / "state.json"
RUNTIME_LOG = LOG_DIR / "v5_runtime.log"
ERROR_LOG = LOG_DIR / "v5_error.log"
DASHBOARD_PATH = DASHBOARD_DIR / "dashboard.html"
ROOT_DASHBOARD_PATH = ROOT_DIR / "dashboard.html"
DAILY_LOOP = SCRIPTS_DIR / "daily_loop.py"


def today() -> str:
    return dt.date.today().isoformat()


def append_runtime(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{now_iso()} {message}"
    print(line)
    with RUNTIME_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def run_command(command: list[str], cwd: Path, timeout: int = 1800) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "ok": result.returncode == 0,
    }


def ensure_layout() -> None:
    for path in [STATE_DIR, LOG_DIR, DASHBOARD_DIR, REPORTS_DIR, DATA_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def latest_matching(path: Path, pattern: str) -> Path | None:
    matches = sorted(path.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def module_result(name: str, success: bool, detail: str, outputs: list[Path]) -> dict[str, Any]:
    return {
        "module": name,
        "success": success,
        "status": "success" if success else "failed",
        "detail": detail,
        "outputs": [str(path) for path in outputs],
        "time": now_iso(),
    }


def daily_report() -> dict[str, Any]:
    append_runtime("START daily_report")
    if not DAILY_LOOP.exists():
        return module_result("daily_report", False, "daily_loop.py not found", [])
    result = run_command([sys.executable, str(DAILY_LOOP)], cwd=SCRIPTS_DIR)
    if result["stdout"]:
        append_runtime("daily_report stdout " + result["stdout"].replace("\n", " | "))
    if result["stderr"]:
        append_runtime("daily_report stderr " + result["stderr"].replace("\n", " | "))
    report = REPORTS_DIR / f"daily_report_{today()}.md"
    success = result["ok"] and report.exists() and report.stat().st_size > 0
    return module_result(
        "daily_report",
        success,
        f"returncode={result['returncode']}; report_exists={report.exists()}",
        [report] if report.exists() else [],
    )


def learning_module() -> dict[str, Any]:
    append_runtime("START learning_module")
    path = latest_matching(DATA_DIR / "learning", f"learning_{today()}_*.md")
    success = bool(path and path.exists() and path.stat().st_size > 0)
    return module_result("learning_report", success, f"learning_output_exists={success}", [path] if path else [])


def portfolio_module() -> dict[str, Any]:
    append_runtime("START portfolio_module")
    path = DATA_DIR / "portfolio" / f"portfolio_update_{today()}.md"
    success = path.exists() and path.stat().st_size > 0
    return module_result("portfolio_update", success, f"portfolio_output_exists={success}", [path] if path.exists() else [])


def side_business_module() -> dict[str, Any]:
    append_runtime("START side_business_module")
    path = DATA_DIR / "side_business" / "service_offer_merchant_support_kb.md"
    success = path.exists() and path.stat().st_size > 0
    return module_result("side_business_update", success, f"side_business_output_exists={success}", [path] if path.exists() else [])


def render_dashboard(state: dict[str, Any]) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    modules = state.get("modules", {})
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(name)}</td>"
        f"<td class=\"{'ok' if item.get('success') else 'fail'}\">{html.escape(item.get('status', 'unknown'))}</td>"
        f"<td>{html.escape(item.get('detail', ''))}</td>"
        f"<td>{html.escape(', '.join(item.get('outputs', [])))}</td>"
        "</tr>"
        for name, item in modules.items()
    )
    embedded = json.dumps(state, ensure_ascii=False)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Career OS v5 Dashboard</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f4f6f8; color: #1f2933; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 26px; margin: 0 0 16px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .card {{ background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 14px; min-height: 72px; }}
    .label {{ color: #586474; font-size: 13px; }}
    .value {{ font-size: 18px; font-weight: 700; margin-top: 8px; overflow-wrap: anywhere; }}
    .ok {{ color: #087443; font-weight: 700; }}
    .fail {{ color: #b42318; font-weight: 700; }}
    .degraded {{ color: #a15c07; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; margin-top: 12px; table-layout: fixed; }}
    th, td {{ border: 1px solid #d8dee8; padding: 10px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }}
    th {{ background: #e9eef5; }}
    code {{ background: #e9eef5; padding: 2px 5px; border-radius: 4px; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} main {{ padding: 18px; }} }}
  </style>
</head>
<body>
<main>
  <h1>AI Career OS v5 Dashboard</h1>
  <section class="grid">
    <div class="card"><div class="label">Last run</div><div class="value">{html.escape(state.get('last_run', ''))}</div></div>
    <div class="card"><div class="label">Status</div><div class="value {html.escape(state.get('status', ''))}">{html.escape(state.get('status', 'unknown'))}</div></div>
    <div class="card"><div class="label">Runtime</div><div class="value">{html.escape(str(state.get('run_time_seconds', '')))}s</div></div>
    <div class="card"><div class="label">GitHub sync</div><div class="value {'ok' if state.get('git_sync', {}).get('success') else 'degraded'}">{html.escape(state.get('git_sync', {}).get('status', 'not_run'))}</div></div>
  </section>
  <h2>Module Status</h2>
  <table>
    <thead><tr><th>Module</th><th>Status</th><th>Detail</th><th>Outputs</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p>State: <code>state/state.json</code> | Runtime log: <code>logs/v5_runtime.log</code> | Error log: <code>logs/v5_error.log</code></p>
</main>
<script>
window.AI_CAREER_OS_V5_STATE = {embedded};
</script>
</body>
</html>
"""
    DASHBOARD_PATH.write_text(page, encoding="utf-8")
    ROOT_DASHBOARD_PATH.write_text(page, encoding="utf-8")


def write_state(state: dict[str, Any]) -> None:
    save_json(STATE_PATH, state)
    save_json(ROOT_STATE_PATH, state)


def run_pipeline() -> dict[str, Any]:
    ensure_layout()
    start = dt.datetime.now()
    previous_state = load_json(STATE_PATH, {})
    state: dict[str, Any] = {
        "version": "v5",
        "last_run": now_iso(),
        "status": "running",
        "previous_status": previous_state.get("status"),
        "modules": {},
        "git_sync": {"success": False, "status": "not_run", "detail": "not run"},
        "scheduler": task_summary(ROOT_DIR),
    }
    write_state(state)
    append_runtime("START run_pipeline version=v5")

    for name, func in [
        ("daily_report", daily_report),
        ("learning_report", learning_module),
        ("portfolio_update", portfolio_module),
        ("side_business_update", side_business_module),
    ]:
        result = safe_module(name, func, ERROR_LOG)
        state["modules"][name] = result
        append_runtime(f"MODULE {'SUCCESS' if result.get('success') else 'FAIL'} {name}: {result.get('detail', result.get('error', ''))}")
        write_state(state)

    modules_ok = all(item.get("success") for item in state["modules"].values())
    state["status"] = "success" if modules_ok else "degraded"
    if not modules_ok:
        mark_degraded(state, "one or more modules failed")

    render_dashboard(state)
    write_state(state)

    git_result = git_sync(ROOT_DIR, ERROR_LOG, message="v5 auto update: daily cycle", retries=3)
    state["git_sync"] = git_result
    if not git_result.get("success"):
        mark_degraded(state, git_result.get("detail", "git sync failed"))

    state["run_time_seconds"] = round((dt.datetime.now() - start).total_seconds(), 2)
    state["last_run"] = now_iso()
    render_dashboard(state)
    write_state(state)
    append_runtime(f"END run_pipeline status={state['status']} run_time_seconds={state['run_time_seconds']}")
    return state


def main() -> int:
    try:
        state = run_pipeline()
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        write_error(ERROR_LOG, "pipeline", exc)
        failed = {
            "version": "v5",
            "last_run": now_iso(),
            "status": "failed",
            "error": repr(exc),
            "traceback": traceback.format_exc(),
        }
        write_state(failed)
        print(json.dumps(failed, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
