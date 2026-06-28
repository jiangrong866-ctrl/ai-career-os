import base64
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "queue" / "github"
STATE = ROOT / "state"
LOGS = ROOT / "logs"


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def log_sync(message: str) -> None:
    LOGS.mkdir(exist_ok=True)
    with (LOGS / "github_sync.log").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(message + "\n")


def github_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ai-career-os",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {body}") from exc


def get_repo(repo: str, token: str) -> dict:
    return github_request("GET", f"/repos/{repo}", token)


def get_ref(repo: str, token: str, branch: str) -> dict:
    safe_branch = urllib.parse.quote(f"heads/{branch}", safe="")
    return github_request("GET", f"/repos/{repo}/git/ref/{safe_branch}", token)


def create_branch(repo: str, token: str, branch: str, base_branch: str) -> dict:
    try:
        return get_ref(repo, token, branch)
    except RuntimeError:
        base_ref = get_ref(repo, token, base_branch)
        sha = base_ref["object"]["sha"]
        return github_request(
            "POST",
            f"/repos/{repo}/git/refs",
            token,
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def create_or_update_file(repo: str, token: str, branch: str, path: str, content: str, message: str) -> dict:
    api_path = f"/repos/{repo}/contents/{urllib.parse.quote(path, safe='/')}"
    sha = None
    try:
        current = github_request("GET", f"{api_path}?ref={urllib.parse.quote(branch, safe='')}", token)
        sha = current.get("sha")
    except RuntimeError:
        sha = None
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    return github_request("PUT", api_path, token, payload)


def create_issue(repo: str, token: str, title: str, body: str) -> dict:
    return github_request("POST", f"/repos/{repo}/issues", token, {"title": title, "body": body})


def create_pr(repo: str, token: str, title: str, head: str, base: str, body: str) -> dict:
    try:
        return github_request(
            "POST",
            f"/repos/{repo}/pulls",
            token,
            {"title": title, "head": head, "base": base, "body": body, "draft": True},
        )
    except RuntimeError as exc:
        # Existing PRs are not fatal for idempotent daemon runs.
        return {"html_url": None, "warning": str(exc)}


def mark_synced(queue_file: Path, item: dict, issue: dict, pr: dict, file_results: list[dict]) -> None:
    item["status"] = "synced"
    item["issue_url"] = issue.get("html_url")
    item["pr_url"] = pr.get("html_url")
    item["file_update_count"] = len(file_results)
    item["synced_at"] = dt.datetime.now().isoformat(timespec="seconds")
    queue_file.write_text(json.dumps(item, ensure_ascii=True, indent=2), encoding="utf-8")


def sync_queue() -> dict:
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    base_branch = os.environ.get("GITHUB_BASE_BRANCH", "main")
    if not token or not repo:
        result = {"ok": False, "reason": "GITHUB_TOKEN and GITHUB_REPOSITORY are required"}
        (STATE / "github_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    placeholder_tokens = {"your-token", "your_github_token", "你的真实 fine-grained token", "你的GitHub fine-grained token"}
    if token.strip() in placeholder_tokens or "fine-grained token" in token:
        result = {"ok": False, "reason": "GITHUB_TOKEN is still a placeholder; set a real GitHub token"}
        (STATE / "github_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    if repo.strip() in {"owner/repo", "username/repo-name"} or "/" not in repo:
        result = {"ok": False, "reason": "GITHUB_REPOSITORY is still a placeholder; use owner/repo"}
        (STATE / "github_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    try:
        token.encode("ascii")
    except UnicodeEncodeError:
        result = {"ok": False, "reason": "GITHUB_TOKEN must be an ASCII token value, not placeholder text"}
        (STATE / "github_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    repo_meta = get_repo(repo, token)
    file_results: list[dict] = []
    queue_results = []
    for queue_file in sorted(QUEUE.glob("sync_*.json")):
        item = json.loads(queue_file.read_text(encoding="utf-8"))
        if item.get("status") == "synced":
            continue
        branch = item.get("branch", "ai-career-os/autonomous-loop")
        message = item.get("commit_message", "daily: AI Career OS update")
        create_branch(repo, token, branch, base_branch)
        for rel_path in item.get("files", []):
            full_path = ROOT / rel_path
            if not full_path.exists():
                continue
            file_results.append(
                create_or_update_file(repo, token, branch, rel_path.replace("\\", "/"), read_text(full_path), message)
            )
        issue = create_issue(repo, token, f"AI Career OS daily run {item.get('date')}", json.dumps(item, indent=2))
        pr = create_pr(repo, token, f"AI Career OS update {item.get('date')}", branch, base_branch, "Automated daily OS update.")
        mark_synced(queue_file, item, issue, pr, file_results)
        queue_results.append({"queue_file": str(queue_file), "issue": issue.get("html_url"), "pr": pr.get("html_url")})

    result = {
        "ok": True,
        "repository": repo,
        "default_branch": repo_meta.get("default_branch"),
        "file_updates": len(file_results),
        "queue_items": queue_results,
    }
    (STATE / "github_sync.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log_sync(json.dumps(result, ensure_ascii=True))
    return result


if __name__ == "__main__":
    print(json.dumps(sync_queue(), indent=2))
