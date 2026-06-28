import json
import os
import urllib.error
import urllib.request

from github_api import load_dotenv


def dispatch() -> dict:
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("AI_CAREER_OS_GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("AI_CAREER_OS_REPOSITORY")
    ref = os.environ.get("GITHUB_BASE_BRANCH", "main")
    workflow = os.environ.get("AI_CAREER_OS_WORKFLOW", "ai-career-os.yml")
    if not token or not repo:
        return {"ok": False, "reason": "GITHUB_TOKEN and GITHUB_REPOSITORY are required for workflow_dispatch"}
    if token.strip() in {"your-token", "your_github_token", "你的真实 fine-grained token"} or "fine-grained token" in token:
        return {"ok": False, "reason": "GITHUB_TOKEN is still a placeholder"}
    if repo.strip() in {"owner/repo", "username/repo-name"} or "/" not in repo:
        return {"ok": False, "reason": "GITHUB_REPOSITORY is still a placeholder; use owner/repo"}
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches",
        data=json.dumps({"ref": ref}).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ai-career-os",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return {"ok": response.status in (200, 201, 202, 204), "status": response.status, "repo": repo, "workflow": workflow}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "reason": exc.read().decode("utf-8", errors="replace")}


if __name__ == "__main__":
    print(json.dumps(dispatch(), indent=2))
