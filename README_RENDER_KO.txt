ABADDON LIVE FEED v1.4.1 · ABADDON LIFE v1.3.0 호환

- Bot v19.6.2 / ABADDON LIFE v1.3.0 / Website v5.1.2 호환 메타데이터 추가
- GET /api/compat 추가
- /health 및 /api/status에 compatibility 정보 포함
- 기존 FiveM QBCore relay, OAuth, Dashboard relay 동작은 유지

ABADDON LIVE FEED v1.3.0 · CHZZK/SOOP DASHBOARD RELAY + OAUTH + LIVE FEED

이 ZIP은 `abaddon-live-feed` Render Web Service용입니다.
`apocalypse-bot` Background Worker에 올리는 파일이 아닙니다.

[Render Web Service]
GitHub 저장소 ROOT에 파일을 올리고 Start Command를 아래처럼 유지하세요.
python live_feed_server.py

필수 Environment
- DISCORD_OAUTH_CLIENT_ID = Discord Application ID
- DISCORD_OAUTH_CLIENT_SECRET = Discord OAuth Client Secret
- DISCORD_OAUTH_REDIRECT_URI = https://abaddon-live-feed.onrender.com/auth/callback
- ABADDON_SITE_URL = https://san01446-ux.github.io/abaddon-policy
- PUBLIC_FEED_ALLOWED_ORIGIN = https://san01446-ux.github.io
- PUBLIC_FEED_RELAY_KEY = apocalypse-bot Background Worker와 동일한 긴 랜덤 문자열

호환 Environment
- 기존 ABADDON_FEED_SECRET만 있다면 PUBLIC_FEED_RELAY_KEY 대신 사용할 수 있습니다.

[apocalypse-bot Background Worker]
- PUBLIC_FEED_RELAY_URL = https://abaddon-live-feed.onrender.com
- PUBLIC_FEED_RELAY_KEY = live-feed와 동일한 값

[Discord Developer Portal]
OAuth2 Redirects에 아래 주소가 정확히 등록되어 있어야 합니다.
https://abaddon-live-feed.onrender.com/auth/callback

[v1.3.0 변경]
- Dashboard relay POST에 CHZZK / SOOP 외부 알림 등록 경로 추가
- 기존 snapshot/cache/빠른 서버 전환 구조는 그대로 유지
- CHZZK / SOOP API Key는 이 live-feed 서비스가 아니라 apocalypse-bot Background Worker에 둡니다.

[v1.2.1 기반 유지]
- /api/dashboard/snapshot 추가: 서버별 읽기 5개를 1개 Worker 요청으로 통합
- snapshot 12초 캐시 + commands 1시간 캐시
- 빠른 서버 이동 시 아직 Worker가 잡지 않은 이전 읽기 요청 supersede
- Worker 버전 변경 시 캐시 자동 초기화
- 1,489+ 명령어 카탈로그 결과가 잘리지 않도록 Worker result JSON 본문 한도 4MB
- 대시보드 relay 대기시간 15초로 단축해 멈춘 요청을 빨리 복구

[v1.2.0 기반 유지]
- Render HEAD /health 요청 200 응답 지원
- 한국어 OAuth -> /dashboard.html
- English OAuth -> /en/dashboard.html
- /api/status + /api/events 공개 LIVE FEED 유지/복구
- Dashboard Relay 인증/요청 큐 구조 유지
- BOT Token은 이 서비스에서 사용하지 않음

[확인 순서]
1. https://abaddon-live-feed.onrender.com/health 접속
2. version 1.4.0 확인
3. BOT 배포 후 worker_online true 확인 (보통 다음 Worker poll/heartbeat 이후)
4. Discord에서 !웹연결진단 또는 !webdiag
5. 홈페이지 Dashboard -> Discord 로그인
6. 서버 선택 -> 설정 / GIF / LIVE / 명령어 탭 확인

보안
- DISCORD_TOKEN은 live-feed 서비스에 넣지 않습니다.
- DISCORD_OAUTH_CLIENT_SECRET은 GitHub Pages 홈페이지에 넣지 않습니다.
- PUBLIC_FEED_RELAY_KEY는 홈페이지에 넣지 않습니다.

============================================================
ABADDON Live Feed v1.4.0 · FiveM/QBCore 양방향 브리지
============================================================
추가 Render 환경변수:
- ABADDON_FIVEM_BRIDGE_SECRET = 충분히 긴 랜덤 문자열 (권장 32자 이상)

이 값은 FiveM server.cfg의 아래 값과 반드시 같아야 합니다.
  set abaddon_bridge_secret "같은_랜덤_문자열"

보안 구조:
- Discord Bot -> Live Feed: PUBLIC_FEED_RELAY_KEY (기존)
- FiveM -> Live Feed: ABADDON_FIVEM_BRIDGE_SECRET (신규)
- MariaDB 비밀번호 / Cfx Registration Key는 브리지에 사용하지 않습니다.

FiveM에서 필요한 server.cfg 예시:
  set abaddon_bridge_enabled "true"
  set abaddon_bridge_relay_url "https://abaddon-live-feed.onrender.com"
  set abaddon_bridge_server_id "abaddon-life-01"
  set abaddon_bridge_guild_id "디스코드_서버_ID"
  set abaddon_bridge_secret "ABADDON_FIVEM_BRIDGE_SECRET와_동일"

Discord 관리자 명령:
  !인생브리지상태
  !인생캐릭터 <서버ID>
  !인생돈지급 <서버ID> <현금|은행> <금액>
  !인생돈회수 <서버ID> <현금|은행> <금액>
  !인생잔액설정 <서버ID> <현금|은행> <금액>
  !인생직업변경 <서버ID> <job> <grade>
  !인생아이템지급 <서버ID> <item> [수량]
  !인생차량지급 <서버ID> <차량모델> [차고]
  !인생역할설정 <직업코드> @역할
  !인생소생 <서버ID>
  !인생공지 <내용>
  !인생킥 <서버ID> [사유]
