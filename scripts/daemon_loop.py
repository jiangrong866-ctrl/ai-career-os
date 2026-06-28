import argparse
import datetime as dt
import json
import time
import traceback
from pathlib import Path

from daily_loop import ROOT, LOGS, STATE, QUEUE, run_daily, write_json, read_json, now_iso
from github_api import sync_queue
from drive_sync import sync_drive


HEARTBEAT = STATE / "daemon_heartbeat.json"
DAEMON_LOG = LOGS / "daemon.log"


def append_daemon_log(message: str) -> None:
    LOGS.mkdir(exist_ok=True)
    with DAEMON_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{now_iso()} {message}\n")


def today_local() -> str:
    return dt.date.today().isoformat()


def should_run(config: dict, once: bool) -> bool:
    if once:
        return True
    state = read_json(STATE / "system_state.json", {})
    today = today_local()
    if state.get("last_successful_date") == today:
        return False
    run_time = config.get("daily_loop_time", "20:30")
    hour, minute = [int(part) for part in run_time.split(":", 1)]
    now = dt.datetime.now()
    return (now.hour, now.minute) >= (hour, minute)


def update_heartbeat(status: str) -> None:
    write_json(
        HEARTBEAT,
        {
            "time": now_iso(),
            "status": status,
            "pid_mode": "python_foreground_or_service",
        },
    )


def process_retry_queue() -> None:
    retry_file = QUEUE / "retry" / "retry_queue.jsonl"
    if not retry_file.exists():
        return
    # The current MVP records retry items and lets the next full run reprocess from source.
    append_daemon_log("retry_queue_detected")


def restore_checkpoint_if_needed() -> None:
    state = read_json(STATE / "system_state.json", {})
    stage = state.get("current_stage")
    if stage and stage != "idle":
        append_daemon_log(f"checkpoint_restore previous_stage={stage}")
        state.setdefault("pending_tasks", []).append(
            {
                "time": now_iso(),
                "type": "checkpoint_restore",
                "previous_stage": stage,
                "action": "rerun_full_pipeline_from_persisted_inputs",
            }
        )
        state["current_stage"] = "idle"
        write_json(STATE / "system_state.json", state)


def run_daemon(once: bool, sleep_seconds: int) -> None:
    config = read_json(ROOT / "config" / "system.json", {})
    append_daemon_log("daemon_started")
    restore_checkpoint_if_needed()
    while True:
        update_heartbeat("alive")
        try:
            process_retry_queue()
            if should_run(config, once):
                today = today_local()
                append_daemon_log(f"daily_run_start date={today}")
                result = run_daily(today)
                try:
                    github_result = sync_queue()
                except Exception as exc:
                    github_result = {"ok": False, "reason": f"github sync exception: {repr(exc)}"}
                    append_daemon_log(github_result["reason"])
                try:
                    drive_result = sync_drive(today)
                except Exception as exc:
                    drive_result = {"ok": False, "reason": f"drive sync exception: {repr(exc)}"}
                    append_daemon_log(drive_result["reason"])
                state = read_json(STATE / "system_state.json", {})
                if result.get("ok"):
                    state["last_successful_date"] = today
                    state["daemon_status"] = "last_run_ok"
                else:
                    state["daemon_status"] = "last_run_failed"
                state["last_github_sync"] = github_result
                state["last_drive_sync"] = drive_result
                if not github_result.get("ok"):
                    state.setdefault("pending_tasks", []).append(
                        {
                            "time": now_iso(),
                            "type": "github_sync",
                            "reason": github_result.get("reason", "unknown"),
                        }
                    )
                if not drive_result.get("ok"):
                    state.setdefault("pending_tasks", []).append(
                        {
                            "time": now_iso(),
                            "type": "drive_sync",
                            "reason": drive_result.get("reason", "unknown"),
                        }
                    )
                write_json(STATE / "system_state.json", state)
                append_daemon_log(f"daily_run_end ok={result.get('ok')}")
                if once:
                    return
        except Exception as exc:
            append_daemon_log(f"daemon_error error={repr(exc)}")
            with (LOGS / "daemon_error.log").open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(traceback.format_exc() + "\n")
        if once:
            return
        time.sleep(sleep_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI Career OS as a persistent daemon loop.")
    parser.add_argument("--once", action="store_true", help="Run one daemon decision cycle for smoke tests.")
    parser.add_argument("--sleep-seconds", type=int, default=300)
    args = parser.parse_args()
    run_daemon(once=args.once, sleep_seconds=args.sleep_seconds)


if __name__ == "__main__":
    main()
