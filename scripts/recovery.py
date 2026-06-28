import datetime as dt
import json
import traceback
from pathlib import Path
from typing import Any, Callable


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_error(error_log: Path, module: str, exc: BaseException | str) -> None:
    message = repr(exc) if not isinstance(exc, str) else exc
    append_line(error_log, f"{now_iso()} module={module} error={message}")
    if not isinstance(exc, str):
        append_line(error_log, traceback.format_exc())


def mark_degraded(state: dict[str, Any], reason: str) -> dict[str, Any]:
    state["status"] = "degraded"
    state.setdefault("degraded_reasons", []).append({"time": now_iso(), "reason": reason})
    return state


def safe_module(
    name: str,
    func: Callable[[], dict[str, Any]],
    error_log: Path,
) -> dict[str, Any]:
    start = dt.datetime.now()
    try:
        result = func()
        result.setdefault("module", name)
        result.setdefault("success", True)
        result["run_time_seconds"] = round((dt.datetime.now() - start).total_seconds(), 2)
        return result
    except Exception as exc:
        write_error(error_log, name, exc)
        return {
            "module": name,
            "success": False,
            "status": "failed",
            "error": repr(exc),
            "run_time_seconds": round((dt.datetime.now() - start).total_seconds(), 2),
            "outputs": [],
            "time": now_iso(),
        }
