import datetime as dt
import html
import json
import subprocess
import sys
import traceback
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parent
ROOT_DIR = SCRIPTS_DIR.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"
REPORTS_DIR = ROOT_DIR / "reports"
STATE_PATH = ROOT_DIR / "state.json"
RUNTIME_LOG = LOG_DIR / "v4_runtime.log"
DASHBOARD_PATH = ROOT_DIR / "dashboard.html"
DAILY_LOOP = SCRIPTS_DIR / "daily_loop.py"


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def today() -> str:
    return dt.date.today().isoformat()


def log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{now()} {message}"
    print(line)
    with RUNTIME_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def run_command(command: list[str], cwd: Path, timeout: int = 1800) -> dict:
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
        "stdout": result.stdout,
        "stderr": result.stderr,
        "ok": result.returncode == 0,
    }


def module_result(name: str, ok: bool, detail: str, outputs: list[str] | None = None) -> dict:
    status = {
        "name": name,
        "success": ok,
        "detail": detail,
        "outputs": outputs or [],
        "time": now(),
    }
    log(f"MODULE {'SUCCESS' if ok else 'FAIL'} {name}: {detail}")
    return status


def run_daily_report() -> dict:
    log("START run_daily_report")
    if not DAILY_LOOP.exists():
        return module_result("daily_report", False, "daily_loop.py not found")
    result = run_command([sys.executable, str(DAILY_LOOP)], cwd=SCRIPTS_DIR)
    report = REPORTS_DIR / f"daily_report_{today()}.md"
    ok = result["ok"] and report.exists()
    detail = f"returncode={result['returncode']}; report_exists={report.exists()}"
    if result["stdout"].strip():
        log("daily_report stdout " + result["stdout"].strip().replace("\n", " | "))
    if result["stderr"].strip():
        log("daily_report stderr " + result["stderr"].strip().replace("\n", " | "))
    return module_result("daily_report", ok, detail, [str(report)] if report.exists() else [])


def run_learning_module() -> dict:
    log("START run_learning_module")
    path = DATA_DIR / "learning" / f"learning_{today()}_customer_success.md"
    ok = path.exists() and path.stat().st_size > 0
    return module_result("learning", ok, f"learning_output_exists={ok}", [str(path)] if path.exists() else [])


def run_portfolio_update() -> dict:
    log("START run_portfolio_update")
    path = DATA_DIR / "portfolio" / f"portfolio_update_{today()}.md"
    ok = path.exists() and path.stat().st_size > 0
    return module_result("portfolio", ok, f"portfolio_output_exists={ok}", [str(path)] if path.exists() else [])


def run_side_business_update() -> dict:
    log("START run_side_business_update")
    path = DATA_DIR / "side_business" / "service_offer_merchant_support_kb.md"
    ok = path.exists() and path.stat().st_size > 0
    return module_result("side_business", ok, f"side_business_output_exists={ok}", [str(path)] if path.exists() else [])


def run_github_sync() -> dict:
    log("START github_sync")
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", "v4 auto sync"],
        ["git", "push"],
    ]
    outputs = []
    for command in commands:
        try:
            result = run_command(command, cwd=ROOT_DIR, timeout=300)
            outputs.append({"command": command, **result})
            if not result["ok"]:
                detail = f"{' '.join(command)} failed: {result['stderr'] or result['stdout']}"
                return module_result("github_sync", False, detail, [])
        except FileNotFoundError:
            return module_result("github_sync", False, "git executable not found", [])
        except Exception as exc:
            return module_result("github_sync", False, repr(exc), [])
    return module_result("github_sync", True, "git add/commit/push completed", [])


def write_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def render_dashboard(state: dict) -> None:
    embedded = json.dumps(state, ensure_ascii=False)
    module_rows = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td class='{ 'ok' if data.get('success') else 'fail' }'>{'SUCCESS' if data.get('success') else 'FAIL'}</td><td>{html.escape(data.get('detail', ''))}</td></tr>"
        for name, data in state.get("modules", {}).items()
    )
    DASHBOARD_PATH.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Career OS v4 Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; background: #f7f8fa; color: #20242a; }}
    main {{ max-width: 980px; margin: 0 auto; }}
    h1 {{ font-size: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
    .card {{ background: #fff; border: 1px solid #d9dee7; border-radius: 8px; padding: 16px; }}
    .ok {{ color: #0b7a3b; font-weight: 700; }}
    .fail {{ color: #b42318; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border: 1px solid #d9dee7; padding: 10px; text-align: left; }}
    th {{ background: #eef2f7; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
<main>
  <h1>AI Career OS v4 Dashboard</h1>
  <div class="grid">
    <section class="card"><strong>Last run</strong><br><span id="last-run">{html.escape(state.get('last_run', ''))}</span></section>
    <section class="card"><strong>Runtime</strong><br><span>{html.escape(str(state.get('run_time_seconds', '')))}s</span></section>
    <section class="card"><strong>Pipeline</strong><br><span class="{'ok' if state.get('success') else 'fail'}">{'SUCCESS' if state.get('success') else 'FAIL'}</span></section>
    <section class="card"><strong>GitHub sync</strong><br><span class="{'ok' if state.get('github_sync', {}).get('success') else 'fail'}">{'SUCCESS' if state.get('github_sync', {}).get('success') else 'FAIL'}</span></section>
  </div>
  <h2>Modules</h2>
  <table>
    <thead><tr><th>Module</th><th>Status</th><th>Detail</th></tr></thead>
    <tbody id="module-body">{module_rows}</tbody>
  </table>
  <p>State file: <code>state.json</code></p>
</main>
<script>
const embeddedState = {embedded};
fetch('state.json').then(r => r.ok ? r.json() : embeddedState).then(s => {{
  document.getElementById('last-run').textContent = s.last_run || embeddedState.last_run;
}}).catch(() => {{}});
</script>
</body>
</html>
""",
        encoding="utf-8",
    )


def run_pipeline() -> dict:
    start = dt.datetime.now()
    log("START run_pipeline")
    modules = {}
    github_sync = {"success": False, "detail": "not run", "outputs": [], "time": now()}

    try:
        for func in (run_daily_report, run_learning_module, run_portfolio_update, run_side_business_update):
            result = func()
            modules[result["name"]] = result
        github_sync = run_github_sync()
        success = all(item.get("success") for item in modules.values())
        run_time = round((dt.datetime.now() - start).total_seconds(), 2)
        state = {
            "version": "v4",
            "last_run": now(),
            "run_time_seconds": run_time,
            "success": success,
            "modules": modules,
            "github_sync": github_sync,
        }
        write_state(state)
        render_dashboard(state)
        log(f"END run_pipeline success={success} run_time_seconds={run_time}")
        return state
    except Exception as exc:
        run_time = round((dt.datetime.now() - start).total_seconds(), 2)
        error = traceback.format_exc()
        log(f"MODULE FAIL pipeline: {repr(exc)}")
        state = {
            "version": "v4",
            "last_run": now(),
            "run_time_seconds": run_time,
            "success": False,
            "modules": modules,
            "github_sync": github_sync,
            "error": error,
        }
        write_state(state)
        render_dashboard(state)
        log("END run_pipeline success=False")
        return state


if __name__ == "__main__":
    result_state = run_pipeline()
    print(json.dumps(result_state, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result_state.get("success") else 1)
