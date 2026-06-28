import datetime as dt
import subprocess
import time
from pathlib import Path
from typing import Any


DEFAULT_GIT = Path(r"C:\Users\1126125669\.workbuddy\vendor\PortableGit\cmd\git.exe")


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def run_command(command: list[str], cwd: Path, timeout: int = 300) -> dict[str, Any]:
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
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "ok": result.returncode == 0,
    }


def _commit_is_noop(result: dict[str, Any]) -> bool:
    combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
    return "nothing to commit" in combined or "working tree clean" in combined


def git_sync(
    repo_root: Path,
    error_log: Path,
    message: str = "v5 auto update: daily cycle",
    retries: int = 3,
    git_exe: Path = DEFAULT_GIT,
) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    if not git_exe.exists():
        detail = f"git executable not found: {git_exe}"
        append_line(error_log, f"{now_iso()} module=git_sync error={detail}")
        return {"success": False, "status": "degraded", "detail": detail, "outputs": outputs}

    add_result = run_command([str(git_exe), "add", "."], repo_root)
    outputs.append(add_result)
    if not add_result["ok"]:
        append_line(error_log, f"{now_iso()} module=git_add error={add_result}")
        return {"success": False, "status": "degraded", "detail": "git add failed", "outputs": outputs}

    commit_result = run_command([str(git_exe), "commit", "-m", message], repo_root)
    outputs.append(commit_result)
    if not commit_result["ok"] and not _commit_is_noop(commit_result):
        append_line(error_log, f"{now_iso()} module=git_commit error={commit_result}")
        return {"success": False, "status": "degraded", "detail": "git commit failed", "outputs": outputs}

    push_result: dict[str, Any] | None = None
    for attempt in range(1, retries + 1):
        push_result = run_command([str(git_exe), "push", "origin", "main"], repo_root, timeout=600)
        push_result["attempt"] = attempt
        outputs.append(push_result)
        if push_result["ok"]:
            return {
                "success": True,
                "status": "success",
                "detail": f"git push origin main succeeded on attempt {attempt}",
                "outputs": outputs,
                "time": now_iso(),
            }
        append_line(error_log, f"{now_iso()} module=git_push attempt={attempt} error={push_result}")
        if attempt < retries:
            time.sleep(5)

    return {
        "success": False,
        "status": "degraded",
        "detail": "git push origin main failed after retries",
        "outputs": outputs,
        "time": now_iso(),
    }
