from collections import defaultdict
from datetime import datetime, timezone, timedelta

from config import CATEGORY_EMOJI


def build_readme(classified: list[dict], all_logs: dict) -> str:
    now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    # 카테고리별 분류
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

    for category, emoji in CATEGORY_EMOJI.items():
        count = len(by_category.get(category, []))
        lines.append(f"| {emoji} {category} | {count} |")

    lines.append("")

    for category in ["승인", "반려", "에러", "알림"]:
        items = by_category.get(category, [])
        if not items:
            continue
        emoji = CATEGORY_EMOJI[category]
        lines.append(f"## {emoji} {category}")
        lines.append("")
        for item in sorted(items, key=lambda x: x["date"], reverse=True):
            lines.append(f"- `{item['date']}` [{item['source']}] {item['subject']}")
        lines.append("")

    # 최근 로그 목록
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

    lines = [
        f"# {date_str} 메일 로그",
        "",
    ]

    for category in ["승인", "반려", "에러", "알림"]:
        items = by_category.get(category, [])
        if not items:
            continue
        emoji = CATEGORY_EMOJI[category]
        lines.append(f"## {emoji} {category} ({len(items)}건)")
        lines.append("")
        for item in sorted(items, key=lambda x: x["date"]):
            lines.append(f"### {item['subject']}")
            lines.append(f"- 발신: `{item['sender']}`")
            lines.append(f"- 시간: `{item['date']}`")
            lines.append(f"- 출처: {item['source']}")
            lines.append("")

    if not any(by_category.values()):
        lines.append("_분류된 메일 없음_")

    return "\n".join(lines)
