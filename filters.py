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
                elif rule["name"] == "Firebase":
                    result.update(_parse_firebase(subject, body))
                elif rule["name"] == "cPanel":
                    result.update(_parse_cpanel(subject))
                elif rule["name"] == "공공데이터":
                    result.update(_parse_publicdata(subject))
                elif rule["name"] == "Lovable":
                    result.update(_parse_lovable(subject))
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


_WORKFLOW_TYPES = [
    ("콘텐츠", ["Auto Publish", "Release due", "Generate Blog", "Generate Pharmacy",
                "Scheduled publish", "Auto Publish Article"]),
    ("데이터",  ["Auto Enrich", "ETL", "bulk-collect", "plant-data", "Daily Pharmacy",
                "Sync TourAPI", "Sync Tour"]),
    ("배포",   ["CI", "Lint", "Deploy", "Gmail Digest"]),
    ("시스템", ["StartupMoneyMap", "Scheduled Search", "backup", "Update dashboard",
               "Apply Drizzle", "Turso", "GSC Sitemap", "SEO Weekly", "dedup"]),
]


def _parse_github(subject: str) -> dict:
    extra = {}
    # [repo] Run failed: workflow - branch (commit)
    m = re.search(r"\[(.+?)\]\s+Run failed:\s+(.+?)\s+-\s+\S+\s+\(([a-f0-9]+)\)", subject)
    if m:
        extra["repo"] = m.group(1)
        extra["workflow"] = m.group(2)
        extra["commit"] = m.group(3)
        wf = m.group(2)
        for wtype, patterns in _WORKFLOW_TYPES:
            if any(p.lower() in wf.lower() for p in patterns):
                extra["workflow_type"] = wtype
                break
        extra.setdefault("workflow_type", "기타")
    return extra


def _parse_vercel(subject: str, body: str) -> dict:
    extra = {}
    # 배포 사이트: body "deploying X to the production"
    m = re.search(r"deploying\s+(\S+)\s+to the production", body, re.IGNORECASE)
    if m:
        extra["site"] = m.group(1)
    # 배포 사이트 fallback: subject "[vercel] Failed production deployment for site.com"
    if "site" not in extra:
        m = re.search(r"deployment for\s+(\S+)", subject, re.IGNORECASE)
        if m:
            extra["site"] = m.group(1).rstrip(".")
    # 배포 사이트 fallback2: body "Your deployment of [project] to ... failed"
    if "site" not in extra:
        m = re.search(r"deployment of\s+(\S+)\s+to", body, re.IGNORECASE)
        if m:
            extra["site"] = m.group(1)
    # 권한 오류: "email attempted to deploy" — 앞에 공백/줄바꿈 필수
    m2 = re.search(r"(?:^|[\s\n<\"])([\w.+-]+@[\w.-]+)\s+attempted to deploy", body, re.IGNORECASE | re.MULTILINE)
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


def _parse_firebase(subject: str, body: str) -> dict:
    extra = {}
    # dSYM 누락: "dSYM 누락 - iOS com.tennisfrens.app 1.0.44 (164)"
    m = re.search(r"([\w.]+)\s+([\d.]+)\s+\((\d+)\)", subject)
    if m:
        extra["app_id"] = m.group(1)
        extra["version"] = m.group(2)
        extra["build"] = m.group(3)
    # UUID 추출
    m2 = re.search(r"([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12})", body, re.IGNORECASE)
    if m2:
        extra["dsym_uuid"] = m2.group(1)
    # 안정성 문제: 장애 건수/사용자 수
    m3 = re.search(r"장애\s*(\d+)건", body)
    if m3:
        extra["crash_count"] = m3.group(1)
    m4 = re.search(r"사용자\s*(\d+)명", body)
    if m4:
        extra["user_count"] = m4.group(1)
    return extra


def _parse_cpanel(subject: str) -> dict:
    extra = {}
    # "Upgrade/Downgrade: alias (domain.kr)"
    m = re.search(r"Upgrade/Downgrade:\s+\S+\s+\((.+?)\)", subject)
    if m:
        extra["domain"] = m.group(1)
    return extra


def _parse_publicdata(subject: str) -> dict:
    extra = {}
    # API명 추출: 대괄호 또는 따옴표 안
    m = re.search(r"['\[「](.{3,40}?)['\]」]", subject)
    if m:
        extra["api_name"] = m.group(1)
    # 만료일 추출
    m2 = re.search(r"(\d{4}[-./]\d{2}[-./]\d{2})", subject)
    if m2:
        extra["expire_date"] = m2.group(1)
    return extra


def _parse_lovable(subject: str) -> dict:
    extra = {}
    # 프로젝트명: "Project X deployed" / "[X] failed"
    m = re.search(r"(?:project\s+)?['\[]?([A-Za-z0-9_-]{3,40})['\]]?\s+(?:deployed|failed|published)", subject, re.IGNORECASE)
    if m:
        extra["project"] = m.group(1)
    return extra
