from collections import defaultdict
from datetime import datetime, timezone, timedelta

from config import CATEGORY_EMOJI

CATEGORY_ORDER = ["승인", "반려", "에러", "경고", "알림"]


def _item_label(item: dict) -> str:
    """각 소스별 한 줄 요약 레이블"""
    src = item["source"]
    cat = item["category"]

    if src == "앱인토스":
        name = item.get("app_name", "?")
        ver = item.get("app_version", "")
        ver_str = f" v{ver}" if ver else ""
        emoji = CATEGORY_EMOJI[cat]
        action = f" ⚠️ 출시 필요" if item.get("action") else ""
        return f"{name}{ver_str} → {emoji} {cat}{action}"

    if src == "GitHub":
        repo = item.get("repo", item["subject"][:40])
        wf = item.get("workflow", "")
        commit = item.get("commit", "")
        commit_str = f" `{commit}`" if commit else ""
        wf_str = f" / {wf}" if wf else ""
        return f"{repo}{wf_str}{commit_str} 실패"

    if src == "Vercel":
        if item.get("unauthorized_user"):
            return f"권한 오류: {item['unauthorized_user']} 배포 시도"
        site = item.get("site", "")
        return f"{site} 배포 실패" if site else "배포 실패"

    if src == "GSC":
        site = item.get("site", "")
        reason = item.get("reason", "")
        if reason:
            return f"{site} → {reason}" if site else reason
        return site or item["subject"][:50]

    if src == "Firebase":
        app = item.get("app_id", "")
        ver = item.get("version", "")
        build = item.get("build", "")
        ver_str = f" {ver}({build})" if ver else ""
        if item["category"] == "경고":
            return f"{app}{ver_str} dSYM 누락"
        crashes = item.get("crash_count", "")
        crash_str = f" 장애 {crashes}건" if crashes else ""
        return f"{app}{ver_str}{crash_str} 안정성 문제"

    if src == "cPanel":
        domain = item.get("domain", "")
        return f"{domain} 계정 변경" if domain else item["subject"][:50]

    return item["subject"][:60]


def build_readme(classified: list[dict], all_logs: dict) -> str:
    now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    by_category = defaultdict(list)
    for item in classified:
        by_category[item["category"]].append(item)

    lines = [
        "# 📬 Gmail Digest",
        f"> 마지막 업데이트: {now} KST",
        "",
        "## 📊 오늘 현황",
        "",
        "| 카테고리 | 건수 |",
        "|---------|------|",
    ]

    for category in CATEGORY_ORDER:
        if category not in CATEGORY_EMOJI:
            continue
        emoji = CATEGORY_EMOJI[category]
        count = len(by_category.get(category, []))
        lines.append(f"| {emoji} {category} | {count} |")

    lines.append("")

    for category in CATEGORY_ORDER:
        items = by_category.get(category, [])
        if not items:
            continue
        emoji = CATEGORY_EMOJI[category]
        lines.append(f"## {emoji} {category}")
        lines.append("")
        for item in sorted(items, key=lambda x: x["date"], reverse=True):
            time_str = item["date"].split(" ")[-1] if " " in item["date"] else item["date"]
            label = _item_label(item)
            lines.append(f"- `{time_str}` [{item['source']}] {label}")
        lines.append("")

    if all_logs:
        lines.append("## 📁 로그 파일")
        lines.append("")
        for date_str in sorted(all_logs.keys(), reverse=True)[:14]:
            lines.append(f"- [{date_str}](logs/{date_str}.md)")
        lines.append("")

    return "\n".join(lines)


def build_daily_log(date_str: str, classified: list[dict]) -> str:
    by_category = defaultdict(list)
    for item in classified:
        by_category[item["category"]].append(item)

    lines = [f"# {date_str} 메일 로그", ""]

    for category in CATEGORY_ORDER:
        items = by_category.get(category, [])
        if not items:
            continue
        emoji = CATEGORY_EMOJI[category]
        lines.append(f"## {emoji} {category} ({len(items)}건)")
        lines.append("")
        for item in sorted(items, key=lambda x: x["date"]):
            label = _item_label(item)
            lines.append(f"### {label}")
            lines.append(f"- 시간: `{item['date']}`")
            lines.append(f"- 발신: `{item['sender']}`")
            # 소스별 추가 정보
            if item["source"] == "앱인토스" and item.get("action"):
                lines.append(f"- 액션: {item['action']}")
            if item["source"] == "GitHub":
                if item.get("repo"):
                    lines.append(f"- 레포: `{item['repo']}`")
                if item.get("workflow"):
                    lines.append(f"- 워크플로우: `{item['workflow']}`")
            if item["source"] == "Vercel" and item.get("site"):
                lines.append(f"- 사이트: `{item['site']}`")
            if item["source"] == "GSC" and item.get("reason"):
                lines.append(f"- 오류: {item['reason']}")
            if item["source"] == "Firebase":
                if item.get("dsym_uuid"):
                    lines.append(f"- UUID: `{item['dsym_uuid']}`")
                if item.get("crash_count"):
                    lines.append(f"- 장애: {item['crash_count']}건 / 사용자 {item.get('user_count', '?')}명")
            if item["source"] == "cPanel" and item.get("domain"):
                lines.append(f"- 도메인: `{item['domain']}`")
            lines.append("")

    if not any(by_category.values()):
        lines.append("_분류된 메일 없음_")

    return "\n".join(lines)
