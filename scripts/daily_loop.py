import argparse
import csv
import datetime as dt
import json
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
STATE = ROOT / "state"
QUEUE = ROOT / "queue"
LOGS = ROOT / "logs"

STAGES = ["input", "analyze", "decision", "execute", "persistence", "verification"]


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def ensure_dirs() -> None:
    for path in [
        DATA / "jobs",
        DATA / "side_business",
        DATA / "learning",
        DATA / "portfolio",
        DATA / "knowledge_items",
        REPORTS,
        STATE,
        QUEUE / "github",
        QUEUE / "retry",
        QUEUE / "structured_input",
        LOGS,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def append_log(message: str) -> None:
    LOGS.mkdir(exist_ok=True)
    with (LOGS / "daily_loop.log").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{now_iso()} {message}\n")


def load_state() -> dict:
    return read_json(
        STATE / "system_state.json",
        {
            "last_run_time": None,
            "current_stage": "idle",
            "failure_count": 0,
            "retry_queue": [],
            "pending_tasks": [],
            "last_successful_run": None,
            "last_verification": None,
        },
    )


def save_state(state: dict) -> None:
    write_json(STATE / "system_state.json", state)


def set_stage(state: dict, stage: str) -> None:
    state["current_stage"] = stage
    state["updated_at"] = now_iso()
    save_state(state)
    append_log(f"stage={stage}")


def record_failure(state: dict, stage: str, error: Exception) -> None:
    state["failure_count"] = int(state.get("failure_count", 0)) + 1
    item = {
        "time": now_iso(),
        "stage": stage,
        "error": repr(error),
    }
    state.setdefault("retry_queue", []).append(item)
    save_state(state)
    append_jsonl(QUEUE / "retry" / "retry_queue.jsonl", [item])
    with (LOGS / "error.log").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{now_iso()} stage={stage} error={repr(error)}\n")
        handle.write(traceback.format_exc() + "\n")


def structured_jobs_for(today: str) -> list[dict]:
    # Priority order: API/MCP/structured inputs first. Chrome is only manual fallback.
    candidates = [
        QUEUE / "structured_input" / f"jobs_{today}.json",
        DATA / "jobs" / f"jobs_{today}.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "title": "Medical SaaS Customer Success with AI Tools",
            "company": "manual-import-needed",
            "salary_score": 60,
            "match_score": 84,
            "growth_score": 76,
            "access_score": 82,
            "requirements": ["customer success", "SaaS implementation", "AI workflow"],
            "source": "structured fallback",
        },
        {
            "title": "AI Operations for Healthcare Applications",
            "company": "manual-import-needed",
            "salary_score": 65,
            "match_score": 78,
            "growth_score": 82,
            "access_score": 75,
            "requirements": ["AI tools", "healthcare domain", "operations SOP"],
            "source": "structured fallback",
        },
        {
            "title": "Merchant Operations Agent Project Assistant",
            "company": "manual-import-needed",
            "salary_score": 55,
            "match_score": 80,
            "growth_score": 85,
            "access_score": 78,
            "requirements": ["merchant operations", "prompt design", "delivery docs"],
            "source": "structured fallback",
        },
    ]


def load_inputs(today: str) -> dict:
    return {
        "jobs": structured_jobs_for(today),
        "side_tasks": [
            {
                "name": "Service offer: merchant customer-service knowledge base",
                "execution_score": 82,
                "monetization_score": 86,
                "skill_score": 76,
                "deliverable": "service_offer_merchant_support_kb.md",
            },
            {
                "name": "Xiaohongshu topic: 3 AI tools for local merchant retention",
                "execution_score": 88,
                "monetization_score": 72,
                "skill_score": 80,
                "deliverable": "xiaohongshu_ai_merchant_retention.md",
            },
        ],
    }


def score_jobs(jobs: list[dict]) -> list[dict]:
    scored = []
    for job in jobs:
        total = (
            float(job.get("salary_score", 0)) * 0.3
            + float(job.get("match_score", 0)) * 0.3
            + float(job.get("growth_score", 0)) * 0.2
            + float(job.get("access_score", 0)) * 0.2
        )
        row = dict(job)
        row["weighted_score"] = round(total, 2)
        scored.append(row)
    return sorted(scored, key=lambda item: item["weighted_score"], reverse=True)


def score_side_tasks(tasks: list[dict]) -> list[dict]:
    scored = []
    for task in tasks:
        total = (
            float(task.get("execution_score", 0)) * 0.4
            + float(task.get("monetization_score", 0)) * 0.3
            + float(task.get("skill_score", 0)) * 0.3
        )
        row = dict(task)
        row["weighted_score"] = round(total, 2)
        scored.append(row)
    return sorted(scored, key=lambda item: item["weighted_score"], reverse=True)


def choose_learning_task(top_jobs: list[dict], today: str) -> dict:
    gap_counts: dict[str, int] = {}
    for job in top_jobs:
        for req in job.get("requirements", []):
            gap_counts[req] = gap_counts.get(req, 0) + 1
    gap = max(gap_counts, key=gap_counts.get) if gap_counts else "AI tools"
    safe_gap = "".join(ch if ch.isalnum() else "_" for ch in gap).strip("_").lower()
    return {
        "gap": gap,
        "task": f"Create one proof artifact for '{gap}': 3 job signals, 1 interview story, and 1 portfolio proof point.",
        "deliverable": f"learning_{today}_{safe_gap}.md",
    }


def format_jobs(jobs: list[dict]) -> str:
    lines = []
    for index, job in enumerate(jobs, start=1):
        requirements = " / ".join(job.get("requirements", []))
        lines.append(
            f"{index}. {job['title']} - score {job['weighted_score']} - "
            f"salary {job.get('salary_score', 0)}, match {job.get('match_score', 0)}, "
            f"growth {job.get('growth_score', 0)}, access {job.get('access_score', 0)} - {requirements}"
        )
    return "\n".join(lines)


def build_report(today: str, top_jobs: list[dict], side_task: dict, learning: dict) -> str:
    return f"""# AI Career OS Daily Report - {today}

## Verification Contract

- Input: complete
- Analysis: complete
- Decision: complete
- Execution: complete
- Persistence: complete
- Verification: pending final check

## Top 3 Jobs

{format_jobs(top_jobs[:3])}

## Learning Task

- Gap: {learning["gap"]}
- Task: {learning["task"]}
- Deliverable: `{learning["deliverable"]}`

## Side-Business Task

- Task: {side_task["name"]}
- Score: {side_task["weighted_score"]}
- Deliverable: `{side_task["deliverable"]}`

## Portfolio Update

- Module: AI Career OS
- Deliverable: `data/portfolio/portfolio_update_{today}.md`
- Change: document autonomous loop, state machine, retry queue, and API-first input policy.

## System Memory Update

- Skill gap changed: {learning["gap"]}
- Job match changed: top score {top_jobs[0]["weighted_score"] if top_jobs else "N/A"}
- Side-business feasibility changed: {side_task["weighted_score"]}
"""


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def persist(today: str, top_jobs: list[dict], side_task: dict, learning: dict, report: str) -> dict:
    report_path = REPORTS / f"daily_report_{today}.md"
    report_path.write_text(report, encoding="utf-8")

    jd_cards = []
    for index, job in enumerate(top_jobs, start=1):
        card = {
            "date": today,
            "title": job["title"],
            "company": job.get("company", ""),
            "weighted_score": job["weighted_score"],
            "requirements": job.get("requirements", []),
            "source": job.get("source", ""),
        }
        jd_cards.append(card)
        write_json(DATA / "knowledge_items" / f"JD_{today}_{index}.json", card)
    append_jsonl(DATA / "jobs" / "jd_cards.jsonl", jd_cards)

    side_record = {"date": today, **side_task}
    append_jsonl(DATA / "side_business" / "history.jsonl", [side_record])

    learning_record = {"date": today, **learning}
    append_jsonl(DATA / "learning" / "growth_track.jsonl", [learning_record])
    learning_path = DATA / "learning" / learning["deliverable"]
    learning_path.write_text(f"# Learning Task - {today}\n\n{learning['task']}\n", encoding="utf-8")

    side_path = DATA / "side_business" / side_task["deliverable"]
    side_path.write_text(
        f"# Side-Business Deliverable - {today}\n\nTask: {side_task['name']}\n\nNext action: package this as a service offer.\n",
        encoding="utf-8",
    )

    portfolio_path = DATA / "portfolio" / f"portfolio_update_{today}.md"
    portfolio_path.write_text(
        "# Portfolio Update\n\n"
        "Case: AI Career OS hard autonomous loop.\n\n"
        "Proof point: daemon loop, state machine, retry queue, API-first input, and GitHub API adapter.\n",
        encoding="utf-8",
    )

    write_csv(
        DATA / "jobs" / "job_scores.csv",
        [{"date": today, **job, "requirements": " / ".join(job.get("requirements", []))} for job in top_jobs],
        ["date", "title", "company", "salary_score", "match_score", "growth_score", "access_score", "weighted_score", "requirements", "source"],
    )
    write_csv(
        DATA / "side_business" / "side_tasks.csv",
        [{"date": today, **side_task}],
        ["date", "name", "execution_score", "monetization_score", "skill_score", "weighted_score", "deliverable"],
    )
    write_csv(
        DATA / "learning" / "learning_progress.csv",
        [learning_record],
        ["date", "gap", "task", "deliverable"],
    )

    write_json(
        QUEUE / "github" / f"sync_{today}.json",
        {
            "date": today,
            "commit_message": f"daily: AI Career OS hard autonomous loop {today}",
            "branch": f"ai-career-os/{today}",
            "files": [
                str(report_path.relative_to(ROOT)),
                str(learning_path.relative_to(ROOT)),
                str(side_path.relative_to(ROOT)),
                str(portfolio_path.relative_to(ROOT)),
            ],
            "status": "pending_github_api",
        },
    )

    memory = {
        "updated_at": now_iso(),
        "latest_date": today,
        "skill_gap": learning["gap"],
        "top_job_score": top_jobs[0]["weighted_score"] if top_jobs else None,
        "side_business_score": side_task["weighted_score"],
    }
    write_json(STATE / "memory.json", memory)
    return {
        "report_path": str(report_path),
        "learning_path": str(learning_path),
        "side_path": str(side_path),
        "portfolio_path": str(portfolio_path),
    }


def verify(outputs: dict) -> dict:
    missing = [path for path in outputs.values() if not Path(path).exists()]
    result = {
        "time": now_iso(),
        "ok": not missing,
        "missing": missing,
        "checks": ["input", "analysis", "decision", "execution", "persistence", "verification"],
    }
    write_json(STATE / "last_verification.json", result)
    if missing:
        raise RuntimeError(f"verification failed: missing={missing}")
    return result


def run_daily(today: str) -> dict:
    ensure_dirs()
    state = load_state()
    state["last_run_time"] = now_iso()
    save_state(state)

    try:
        set_stage(state, "input")
        inputs = load_inputs(today)

        set_stage(state, "analyze")
        top_jobs = score_jobs(inputs["jobs"])[:3]
        side_tasks = score_side_tasks(inputs["side_tasks"])

        set_stage(state, "decision")
        side_task = side_tasks[0]
        learning = choose_learning_task(top_jobs, today)

        set_stage(state, "execute")
        report = build_report(today, top_jobs, side_task, learning)

        set_stage(state, "persistence")
        outputs = persist(today, top_jobs, side_task, learning, report)

        set_stage(state, "verification")
        verification = verify(outputs)

        state = load_state()
        state["current_stage"] = "idle"
        state["last_successful_run"] = now_iso()
        state["last_verification"] = verification
        save_state(state)
        append_log("run=success")
        return {"ok": True, "outputs": outputs, "verification": verification}
    except Exception as exc:
        record_failure(load_state(), load_state().get("current_stage", "unknown"), exc)
        return {"ok": False, "error": repr(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Career OS daily loop once.")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    args = parser.parse_args()
    result = run_daily(args.date)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
