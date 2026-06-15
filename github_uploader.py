import base64
import subprocess
import json
import requests


def _get_token() -> str:
    # GitHub Actions에서는 GITHUB_TOKEN 환경변수 우선 사용
    import os
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    return result.stdout.strip()


def _api_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_sha(token: str, owner: str, repo: str, path: str) -> str | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_api_headers(token))
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def _list_files(token: str, owner: str, repo: str, folder: str) -> list[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}"
    resp = requests.get(url, headers=_api_headers(token))
    if resp.status_code == 200:
        return [f["name"] for f in resp.json() if f["type"] == "file"]
    return []


def upsert_file(owner: str, repo: str, path: str, content: str, message: str):
    token = _get_token()
    sha = _get_sha(token, owner, repo, path)
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    payload = {"message": message, "content": encoded}
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=_api_headers(token), json=payload)
    resp.raise_for_status()


def list_log_dates(owner: str, repo: str) -> dict:
    token = _get_token()
    files = _list_files(token, owner, repo, "logs")
    return {f.replace(".md", ""): True for f in files if f.endswith(".md")}


def ensure_repo_exists(owner: str, repo: str):
    token = _get_token()
    url = f"https://api.github.com/repos/{owner}/{repo}"
    resp = requests.get(url, headers=_api_headers(token))
    if resp.status_code == 404:
        create_url = "https://api.github.com/user/repos"
        payload = {
            "name": repo,
            "description": "Gmail 자동 정리 — 앱인토스 승인/반려, 에러, 알림",
            "private": False,
            "auto_init": True,
        }
        r = requests.post(create_url, headers=_api_headers(token), json=payload)
        r.raise_for_status()
        print(f"레포 생성 완료: https://github.com/{owner}/{repo}")
    else:
        print(f"레포 확인 완료: https://github.com/{owner}/{repo}")
