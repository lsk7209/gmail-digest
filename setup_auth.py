"""
최초 1회 실행: Gmail OAuth 토큰 발급
  python setup_auth.py

브라우저가 열리면 lsk7209@gmail.com 계정으로 로그인 후 허용.
token.json 생성 후 GitHub Actions용 base64 출력.
"""
import base64
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from config import GMAIL_SCOPES, OAUTH_CLIENT_FILE, TOKEN_FILE


def main():
    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_FILE, GMAIL_SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"\n토큰 저장 완료: {TOKEN_FILE}")

    # GitHub Secret 등록용 base64 출력
    token_b64 = base64.b64encode(Path(TOKEN_FILE).read_bytes()).decode()
    print("\n=== GitHub Secret 값 (GMAIL_TOKEN) ===")
    print(token_b64)
    print("\nGitHub → Settings → Secrets → New repository secret 에 붙여넣기")
    print("Secret name: GMAIL_TOKEN")


if __name__ == "__main__":
    main()
