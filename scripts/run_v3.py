import datetime as dt
import subprocess
import sys
import traceback
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "run_v3.log"
TASK_LOG_FILE = LOG_DIR / "v3_task.log"
DAILY_LOOP = SCRIPTS_DIR / "daily_loop.py"


def timestamp() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def write_log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{timestamp()} {message}"
    print(line)
    for path in (LOG_FILE, TASK_LOG_FILE):
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")


def main() -> int:
    write_log("AI Career OS v3 start")
    write_log(f"cwd={SCRIPTS_DIR}")
    write_log(f"daily_loop={DAILY_LOOP}")

    if not DAILY_LOOP.exists():
        write_log("ERROR daily_loop.py not found")
        return 2

    try:
        result = subprocess.run(
            [sys.executable, str(DAILY_LOOP)],
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
        write_log(f"returncode={result.returncode}")
        write_log("stdout_begin")
        if result.stdout.strip():
            for line in result.stdout.splitlines():
                write_log(f"stdout {line}")
        else:
            write_log("stdout <empty>")
        write_log("stdout_end")

        write_log("stderr_begin")
        if result.stderr.strip():
            for line in result.stderr.splitlines():
                write_log(f"stderr {line}")
        else:
            write_log("stderr <empty>")
        write_log("stderr_end")

        if result.returncode == 0:
            write_log("AI Career OS v3 completed successfully")
        else:
            write_log("AI Career OS v3 completed with errors")
        write_log(f"completed_at={timestamp()}")
        return result.returncode
    except Exception as exc:
        write_log(f"EXCEPTION {repr(exc)}")
        for line in traceback.format_exc().splitlines():
            write_log(f"trace {line}")
        write_log(f"completed_at={timestamp()}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
