import os
from datetime import datetime, timezone, timedelta

import requests

from config import FILTERS


APPIN_TOSS_SOURCE = FILTERS[0]["name"]


def _dashboard_config() -> tuple[str | None, str | None, str | None]:
    base_url = os.environ.get("AIT_DASH_URL", "").rstrip("/")
    webhook_url = (
        os.environ.get("AIT_ISSUE_WEBHOOK_URL")
        or os.environ.get("DASHBOARD_WEBHOOK_URL")
        or ""
    ).rstrip("/")
    key = (
        os.environ.get("AIT_API_KEY")
        or os.environ.get("INGEST_API_KEY")
        or os.environ.get("DASHBOARD_API_KEY")
    )

    issue_url = None
    heartbeat_url = None
    if base_url:
        issue_url = f"{base_url}/api/ingest/issue"
        heartbeat_url = f"{base_url}/api/ingest/heartbeat"
    elif webhook_url:
        issue_url = webhook_url
        if webhook_url.endswith("/api/ingest/issue"):
            heartbeat_url = webhook_url[: -len("/issue")] + "/heartbeat"

    return issue_url, heartbeat_url, (key or None)


def _iso_kst(value: str) -> str:
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=timezone(timedelta(hours=9))).isoformat()
    except Exception:
      return datetime.now(timezone(timedelta(hours=9))).isoformat()


def _is_appin_toss(item: dict) -> bool:
    text = f"{item.get('subject', '')}\n{item.get('body', '')}"
    sender = item.get("sender", "")
    return (
        item.get("source") == APPIN_TOSS_SOURCE
        or "business.toss.im" in sender.lower()
        or "apps-in-toss" in sender.lower()
        or "앱인토스" in text
        or "Apps in Toss" in text
        or "AppsInToss" in text
    )


def post_to_dashboard(items: list[dict]) -> dict:
    issue_url, heartbeat_url, api_key = _dashboard_config()
    if not issue_url or not api_key:
        return {"enabled": False, "posted": 0, "skipped": 0, "failed": 0}

    posted = 0
    skipped = 0
    failed = 0

    for item in items:
        if not _is_appin_toss(item):
            skipped += 1
            continue

        payload = {
            "gmail_id": item.get("id"),
            "from": item.get("sender"),
            "subject": item.get("subject") or "(no subject)",
            "snippet": (item.get("body") or "")[:240],
            "body": "\n".join(
                part
                for part in [
                    item.get("subject") or "",
                    item.get("app_name") or "",
                    item.get("app_version") or "",
                    item.get("body") or "",
                ]
                if part
            )[:8000],
            "received_at": _iso_kst(item.get("date", "")),
        }

        try:
            response = requests.post(
                issue_url,
                headers={"x-api-key": api_key},
                json=payload,
                timeout=20,
            )
            if response.ok:
                data = response.json()
                if data.get("skipped"):
                    skipped += 1
                else:
                    posted += 1
            else:
                failed += 1
                print(f"  dashboard ingest failed {response.status_code}: {response.text[:160]}")
        except Exception as exc:
            failed += 1
            print(f"  dashboard ingest exception: {exc}")

    if heartbeat_url:
        _send_heartbeat(heartbeat_url, api_key)
    return {"enabled": True, "posted": posted, "skipped": skipped, "failed": failed}


def _send_heartbeat(heartbeat_url: str, api_key: str) -> None:
    try:
        requests.post(
            heartbeat_url,
            headers={"x-api-key": api_key},
            json={"source": "gmail", "at": datetime.now(timezone.utc).isoformat()},
            timeout=10,
        )
    except Exception as exc:
        print(f"  dashboard heartbeat exception: {exc}")
