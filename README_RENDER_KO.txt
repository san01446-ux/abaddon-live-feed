ABADDON LIVE FEED v1.1.0 · DASHBOARD RELAY

이 ZIP은 `abaddon-live-feed` Render Web Service용입니다.
`apocalypse-bot` Background Worker에 올리는 파일이 아닙니다.

[Render Web Service]
Root에 이 파일들을 올리고 Start Command를 다음처럼 설정하세요.
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
OAuth2 Redirects에 아래 주소가 등록되어 있어야 합니다.
https://abaddon-live-feed.onrender.com/auth/callback

[확인 순서]
1. https://abaddon-live-feed.onrender.com/health 접속
2. JSON에 worker_online true 확인 (봇 배포 후 최대 약 15초)
3. Discord에서 !웹연결진단
4. 홈페이지 Dashboard -> Discord 로그인
5. 서버 선택 -> 설정 저장

보안
- DISCORD_TOKEN은 live-feed 서비스에 넣지 않습니다.
- DISCORD_OAUTH_CLIENT_SECRET은 GitHub Pages 홈페이지에 넣지 않습니다.
- PUBLIC_FEED_RELAY_KEY는 홈페이지에 넣지 않습니다.
