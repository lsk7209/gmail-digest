from collections import defaultdict
from datetime import datetime, timezone, timedelta

from config import CATEGORY_EMOJI

CATEGORY_ORDER = ["승인", "반려", "에러", "경고", "알림"]


def _item_label(item: dict) -> str:
    src = item["source"]
    cat = item["category"]

    if src == "앱인토스":
        name = item.get("app_name", "?")
        ver = item.get("app_version", "")
        ver_str = f" v{ver}" if ver else ""
        emoji = CATEGORY_EMOJI[cat]
        action = " ⚠️ 출시 업데이트 필요" if item.get("release_update_required") else ""
        return f"{name}{ver_str} → {emoji} {cat}{action}"

    if src == "GitHub":
        repo = item.get("repo", item["subject"][:40])
        wf = item.get("workflow", "")
        wtype = item.get("workflow_type", "")
        wtype_str = f"[{wtype}] " if wtype else ""
        commit = item.get("commit", "")
        commit_str = f" `{commit[:7]}`" if commit else ""
        return f"{repo} / {wtype_str}{wf}{commit_str}"

    if src == "Vercel":
        if item.get("unauthorized_user"):
            return f"권한 오류: {item['unauthorized_user']} 배포 시도"
        site = item.get("site", "")
        return f"{site} 배포 실패" if site else "배포 실패"

    if src == "GSC":
        site = item.get("site", "")
        reason = item.get("reason", "")
        if reason:
            return f"{site} — {reason}" if site else reason
        return site or item["subject"][:50]

    if src == "Firebase":
        app = item.get("app_id", "")
        ver = item.get("version", "")
        build = item.get("build", "")
        ver_str = f" {ver}({build})" if ver else ""
        if cat == "경고":
            return f"{app}{ver_str} dSYM 누락"
        crashes = item.get("crash_count", "")
        crash_str = f" 장애 {crashes}건" if crashes else ""
        return f"{app}{ver_str}{crash_str} 안정성 문제"

    if src == "cPanel":
        domain = item.get("domain", "")
        return f"{domain} 계정 변경" if domain else item["subject"][:50]

    if src == "AdSense":
        return item["subject"][:60]

    if src == "PlayConsole":
        return item["subject"][:60]

    if src == "공공데이터":
        api = item.get("api_name", "")
        expire = item.get("expire_date", "")
        if api and expire:
            return f"{api} 만료 예정 ({expire})"
        return api or item["subject"][:60]

    if src == "Lovable":
        project = item.get("project", "")
        return f"{project} — {item['subject'][:40]}" if project else item["subject"][:60]

    return item["subject"][:60]


def _dedup_github(items: list[dict]) -> list[dict]:
    """같은 repo+workflow를 묶어 count 추가, 최신 1건만 대표로 남김"""
    seen: dict[tuple, dict] = {}
    for item in sorted(items, key=lambda x: x["date"]):
        key = (item.get("repo", ""), item.get("workflow", ""))
        if key in seen:
            seen[key]["_count"] = seen[key].get("_count", 1) + 1
            seen[key]["commit"] = item.get("commit", "")  # 최신 커밋
        else:
            seen[key] = {**item, "_count": 1}
    return list(seen.values())


def build_readme(classified: list[dict], all_logs: dict) -> str:
    now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    by_category: dict[str, list] = defaultdict(list)
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
    for cat in CATEGORY_ORDER:
        if cat not in CATEGORY_EMOJI:
            continue
        count = len(by_category.get(cat, []))
        lines.append(f"| {CATEGORY_EMOJI[cat]} {cat} | {count} |")
    lines.append("")

    for cat in CATEGORY_ORDER:
        items = by_category.get(cat, [])
        if not items:
            continue
        emoji = CATEGORY_EMOJI[cat]

        # GitHub 에러는 테이블로 중복 제거
        gh_items = [x for x in items if x["source"] == "GitHub"]
        other_items = [x for x in items if x["source"] != "GitHub"]

        lines.append(f"## {emoji} {cat}")
        lines.append("")

        if gh_items:
            deduped = _dedup_github(gh_items)
            # 워크플로우 타입별 정렬
            deduped.sort(key=lambda x: (x.get("workflow_type", "기타"), x.get("repo", "")))
            lines.append("### 🔴 GitHub Actions 실패")
            lines.append("")
            lines.append("| 레포 | 워크플로우 | 타입 | 횟수 | 커밋 |")
            lines.append("|------|-----------|------|------|------|")
            for item in deduped:
                repo = item.get("repo", "").replace("lsk7209/", "")
                wf = item.get("workflow", "")
                wtype = item.get("workflow_type", "기타")
                cnt = item.get("_count", 1)
                commit = item.get("commit", "")[:7]
                cnt_str = f"**{cnt}회**" if cnt > 1 else "1회"
                lines.append(f"| `{repo}` | {wf} | {wtype} | {cnt_str} | `{commit}` |")
            lines.append("")

        for item in sorted(other_items, key=lambda x: x["date"], reverse=True):
            time_str = item["date"].split(" ")[-1] if " " in item["date"] else item["date"]
            label = _item_label(item)
            lines.append(f"- `{time_str}` [{item['source']}] {label}")
        if other_items:
            lines.append("")

    if all_logs:
        lines.append("## 📁 로그 파일")
        lines.append("")
        for date_str in sorted(all_logs.keys(), reverse=True)[:14]:
            lines.append(f"- [{date_str}](logs/{date_str}.md)")
        lines.append("")

    return "\n".join(lines)


def build_daily_log(date_str: str, classified: list[dict]) -> str:
    by_category: dict[str, list] = defaultdict(list)
    for item in classified:
        by_category[item["category"]].append(item)

    lines = [f"# {date_str} 메일 로그", ""]

    for cat in CATEGORY_ORDER:
        items = by_category.get(cat, [])
        if not items:
            continue
        emoji = CATEGORY_EMOJI[cat]

        gh_items = [x for x in items if x["source"] == "GitHub"]
        other_items = [x for x in items if x["source"] != "GitHub"]

        lines.append(f"## {emoji} {cat} ({len(items)}건)")
        lines.append("")

        # GitHub: 타입별 그룹 → 중복 제거 테이블
        if gh_items:
            deduped = _dedup_github(gh_items)
            by_type: dict[str, list] = defaultdict(list)
            for item in deduped:
                by_type[item.get("workflow_type", "기타")].append(item)

            for wtype in ["콘텐츠", "데이터", "시스템", "배포", "기타"]:
                wtype_items = by_type.get(wtype, [])
                if not wtype_items:
                    continue
                lines.append(f"### GitHub [{wtype}] ({sum(x.get('_count',1) for x in wtype_items)}건)")
                lines.append("")
                lines.append("| 레포 | 워크플로우 | 횟수 | 커밋 |")
                lines.append("|------|-----------|------|------|")
                for item in sorted(wtype_items, key=lambda x: -x.get("_count", 1)):
                    repo = item.get("repo", "").replace("lsk7209/", "")
                    wf = item.get("workflow", "")
                    cnt = item.get("_count", 1)
                    commit = item.get("commit", "")[:7]
                    cnt_str = f"**{cnt}회**" if cnt > 1 else "1회"
                    lines.append(f"| `{repo}` | {wf} | {cnt_str} | `{commit}` |")
                lines.append("")

        # 나머지 소스: 개별 항목
        for item in sorted(other_items, key=lambda x: x["date"]):
            label = _item_label(item)
            lines.append(f"### {label}")
            lines.append(f"- 시간: `{item['date']}`")
            lines.append(f"- 발신: `{item['sender']}`")
            if item["source"] == "앱인토스" and item.get("action"):
                lines.append(f"- 액션: {item['action']}")
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
