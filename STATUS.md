# Status | 마지막: 2026-06-15

## 현재 작업
자동화 완료 — GitHub Actions 6시간마다 실행 중

## 최근 변경 (최근 5개만)
- 06-15: AdSense/PlayConsole/공공데이터/Lovable 필터 추가
- 06-15: Vercel HTML 이메일 파싱 개선 (text/html fallback, 정규식 강화)
- 06-15: GitHub 중복 제거 + 워크플로우 타입별 그룹화 (README 테이블)
- 06-15: filters.py workflow_type 분류 (콘텐츠/데이터/시스템/배포/기타)
- 06-15: 전체 시스템 구축 완료 (Gmail → GitHub 자동 정리)

## TODO
- [ ] Vercel 사이트명/unauthorized_user 파싱 실제 이메일로 검증
- [ ] AdSense/PlayConsole/공공데이터/Lovable 분류 결과 확인 (이메일 수신 시)

## 결정사항
- GitHub API 직접 호출(requests): PyGithub 대신 — 의존성 최소화
- GitHub 에러 중복 제거: repo+workflow 기준, README는 테이블로
- token.json: GitHub Secret GMAIL_TOKEN (base64)으로만 관리

## 주의
- token.json 절대 커밋 금지 (.gitignore 포함)
- lint/build는 Stop hook 자동 처리 — 직접 호출 금지
- FETCH_DAYS=1 → 최근 1일치 수집 (Actions 6시간 주기 맞춤)
- GMAIL_TOKEN_FILE=token.json 환경변수 필수 (Actions Linux 경로)
