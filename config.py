import os

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
# 로컬: D:\env\ 사용, GitHub Actions: 환경변수로 덮어씀
OAUTH_CLIENT_FILE = os.environ.get("OAUTH_CLIENT_FILE", r"D:\env\adsense_oauth_client.json")
# 로컬: 절대 경로, Actions: 워크스페이스 루트의 token.json
TOKEN_FILE = os.environ.get("GMAIL_TOKEN_FILE", r"D:\gmail-auto\token.json")

GITHUB_OWNER = "lsk7209"
GITHUB_REPO = "gmail-digest"

# 최근 며칠치 메일을 가져올지 (GitHub Actions 실행 주기보다 넉넉하게)
FETCH_DAYS = 1

FILTERS = [
    {
        "name": "앱인토스",
        "sender_contains": "토스 비즈니스",
        "subject_prefix": "[앱인토스]",
        "categories": {
            "승인": ["승인됐어요"],
            "반려": ["반려됐어요"],
            "에러": ["오류가 발생", "실패했어요"],
        },
    },
    {
        "name": "GitHub",
        "sender_contains": "github",
        "categories": {
            "에러": ["Run failed", "workflow run", "run failed"],
        },
    },
    {
        "name": "Vercel",
        "sender_contains": "vercel",
        "categories": {
            "에러": [
                "Failed production deployment",
                "Failed production deployments",
                "error deploying",
                "not a member of the team",  # 권한 오류
                "attempted to deploy",
            ],
        },
    },
    {
        "name": "GSC",
        "sender_contains": "Google Search Console",
        "categories": {
            "경고": ["색인이 생성되지 않", "새로운 이유로", "색인 생성 오류", "index coverage"],
            "알림": ["트래픽 모니터링", "Search traffic", "search traffic"],
        },
    },
    {
        "name": "Firebase",
        "sender_contains": "firebase-noreply@google.com",
        "categories": {
            "에러": ["안정성 문제", "발생 빈도", "급속도로 증가", "stability issue", "crash rate"],
            "경고": ["dSYM", "누락", "missing dSYM"],
        },
    },
    {
        "name": "cPanel",
        "sender_contains": "serverhostgroup",
        "categories": {
            "알림": ["Upgrade/Downgrade", "Account updated"],
        },
    },
]

CATEGORY_EMOJI = {
    "승인": "✅",
    "반려": "❌",
    "에러": "🚨",
    "경고": "⚠️",
    "알림": "📊",
}
