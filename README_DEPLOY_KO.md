# ABADDON 실시간 피드 Web Service v4.3.2.1

이 서비스는 Discord 봇으로 로그인하지 않습니다. Background Worker가 공개 가능한 강화 이정표·운영 공지만 비밀키로 전송하면, 홈페이지가 `/api/status`와 `/api/events`를 읽습니다.

## Render 설정

- 서비스 종류: Web Service
- Runtime: Python 3
- Build Command: `echo ready`
- Start Command: `python -m abaddon_feed_service.app`
- Health Check Path: `/healthz`

환경변수:

- `ABADDON_FEED_SECRET`: 32자 이상 임의 문자열. Background Worker의 `PUBLIC_FEED_RELAY_KEY`와 완전히 같아야 합니다.
- `PUBLIC_FEED_ALLOWED_ORIGIN`: GitHub Pages 주소. 예: `https://사용자명.github.io`
- `FEED_OFFLINE_AFTER_SECONDS`: `150` 권장
- `FEED_DATA_FILE`: 선택. 유료 Persistent Disk를 붙였을 때만 `/var/data/abaddon_feed.json` 사용 권장

이 서비스에는 `DISCORD_TOKEN`, `DATA_FILE`, `survival_data.json`을 넣지 않습니다.
