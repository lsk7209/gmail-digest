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
    {
        "name": "AdSense",
        "sender_contains": "adsense",
        "categories": {
            "경고": ["정책 위반", "policy violation", "위반이 감지", "ads.txt", "광고 게재 제한", "serving limit"],
            "알림": ["지급", "payment", "수익", "earnings", "월간 보고"],
        },
    },
    {
        "name": "PlayConsole",
        "sender_contains": "play-developer",
        "categories": {
            "경고": ["정책 위반", "policy violation", "앱이 삭제", "app removed", "suspended"],
            "에러": ["비정상 종료", "crash", "ANR", "fatal"],
            "알림": ["새 리뷰", "new review", "업데이트", "승인", "published"],
        },
    },
    {
        "name": "공공데이터",
        "sender_contains": "data.go.kr",
        "categories": {
            "경고": ["만료", "expired", "만료 예정", "서비스키", "API키", "활용 중지"],
            "알림": ["승인", "신청", "변경", "안내"],
        },
    },
    {
        "name": "Lovable",
        "sender_contains": "lovable.dev",
        "categories": {
            "에러": ["failed", "error", "실패"],
            "알림": ["deployed", "published", "usage", "limit"],
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
