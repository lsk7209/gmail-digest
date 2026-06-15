import sys
import io
from datetime import datetime, timezone, timedelta

# Windows 콘솔 UTF-8 출력
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import FETCH_DAYS, GITHUB_OWNER, GITHUB_REPO
from gmail_client import fetch_emails
from filters import classify_email
from formatter import build_readme, build_daily_log
from github_uploader import ensure_repo_exists, upsert_file, list_log_dates


def main():
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    print(f"[{today}] Gmail 수집 시작...")

    ensure_repo_exists(GITHUB_OWNER, GITHUB_REPO)

    emails = fetch_emails(days=FETCH_DAYS)
    print(f"  수신 메일 {len(emails)}건 조회")

    classified = []
    for em in emails:
        result = classify_email(em)
        if result:
            classified.append(result)

    print(f"  분류된 메일 {len(classified)}건")
    for item in classified:
        print(f"    [{item['category']}] {item['source']} | {item['subject'][:60]}")

    # 날짜별 로그 업로드
    daily_log = build_daily_log(today, classified)
    upsert_file(
        GITHUB_OWNER, GITHUB_REPO,
        f"logs/{today}.md",
        daily_log,
        f"📬 {today} 메일 로그 갱신",
    )
    print(f"  logs/{today}.md 업로드 완료")

    # README 갱신 (기존 로그 목록 포함)
    all_logs = list_log_dates(GITHUB_OWNER, GITHUB_REPO)
    readme = build_readme(classified, all_logs)
    upsert_file(
        GITHUB_OWNER, GITHUB_REPO,
        "README.md",
        readme,
        f"📊 README 갱신 ({today})",
    )
    print("  README.md 업로드 완료")
    print(f"완료: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}")


if __name__ == "__main__":
    main()
