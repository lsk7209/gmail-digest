import re
from config import FILTERS


def classify_email(email: dict) -> dict | None:
    subject = email["subject"]
    sender = email["sender"]
    body = email["body"]
    text = f"{subject} {body}".lower()

    for rule in FILTERS:
        if rule["sender_contains"].lower() not in sender.lower():
            continue

        if "subject_prefix" in rule and rule["subject_prefix"] not in subject:
            continue

        for category, keywords in rule["categories"].items():
            if any(kw.lower() in text for kw in keywords):
                result = {**email, "source": rule["name"], "category": category}
                if rule["name"] == "앱인토스":
                    result.update(_parse_appin_toss(subject, category))
                elif rule["name"] == "GitHub":
                    result.update(_parse_github(subject))
                elif rule["name"] == "Vercel":
                    result.update(_parse_vercel(subject, body))
                elif rule["name"] == "GSC":
                    result.update(_parse_gsc(subject, body))
                elif rule["name"] == "cPanel":
                    result.update(_parse_cpanel(subject))
                return result

    return None


def _parse_appin_toss(subject: str, category: str) -> dict:
    extra = {}

    # 앱 이름: '앱이름' 앱의 / '앱이름' 앱 정보가
    m = re.search(r"'(.+?)'\s+앱의", subject)
    if not m:
        m = re.search(r"'(.+?)'\s+앱\s+정보가", subject)
    if m:
        extra["app_name"] = m.group(1)

    # 버전: YYYYMMDD-N
    m = re.search(r"(\d{8}-\d+)\s+버전", subject)
    if m:
        extra["app_version"] = m.group(1)

    if category == "승인":
        extra["action"] = "출시 필요 — 콘솔에서 [출시하기] 클릭"

    return extra


def _parse_github(subject: str) -> dict:
    extra = {}
    # [repo] Run failed: workflow - branch (commit)
    m = re.search(r"\[(.+?)\]\s+Run failed:\s+(.+?)\s+-\s+\S+\s+\(([a-f0-9]+)\)", subject)
    if m:
        extra["repo"] = m.group(1)
        extra["workflow"] = m.group(2)
        extra["commit"] = m.group(3)
    return extra


def _parse_vercel(subject: str, body: str) -> dict:
    extra = {}
    # 배포 사이트: "deploying X to the production"
    m = re.search(r"deploying\s+(\S+)\s+to the production", body, re.IGNORECASE)
    if m:
        extra["site"] = m.group(1)
    # 권한 오류: "email attempted to deploy"
    m2 = re.search(r"([\w.+-]+@[\w.-]+)\s+attempted to deploy", body, re.IGNORECASE)
    if m2:
        extra["unauthorized_user"] = m2.group(1)
    # 팀명: "on team 'xxx'"
    m3 = re.search(r"team\s+'([^']+)'", subject, re.IGNORECASE)
    if m3:
        extra["team"] = m3.group(1)
    return extra


def _parse_gsc(subject: str, body: str) -> dict:
    extra = {}
    # 사이트 URL
    m = re.search(r"https?://([^\s/]+)", subject)
    if m:
        extra["site"] = m.group(1)
    # 색인 오류 사유: "확인했습니다" 이후 첫 비어있지 않은 줄
    parts = re.split(r"확인했습니다\.?\s*", body, maxsplit=1)
    if len(parts) > 1:
        for line in parts[1].splitlines():
            line = line.strip()
            if line and len(line) < 80:
                extra["reason"] = line
                break
    return extra


def _parse_cpanel(subject: str) -> dict:
    extra = {}
    # "Upgrade/Downgrade: alias (domain.kr)"
    m = re.search(r"Upgrade/Downgrade:\s+\S+\s+\((.+?)\)", subject)
    if m:
        extra["domain"] = m.group(1)
    return extra
