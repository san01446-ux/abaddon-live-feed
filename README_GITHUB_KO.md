# ABADDON Live Feed v1.5.0 · GitHub 배포용

이 ZIP은 저장소 **루트에 그대로 덮어쓰는** 형태입니다. `live_feed_server.py`, `requirements.txt`, `render.yaml`이 같은 루트에 있어야 합니다.

## 업데이트
1. 기존 Live Feed GitHub 저장소 백업/브랜치 생성
2. 이 ZIP 내용을 저장소 루트에 덮어쓰기
3. commit / push
4. 저장소와 연결된 Web Service의 자동 배포 완료 확인
5. `/health`에서 `version: 1.5.0` 확인
6. `/api/bridge/diagnostics`에서 `fivem_bridge_configured: true` 확인

## 반드시 맞아야 하는 값
- Live Feed `PUBLIC_FEED_RELAY_KEY` = ABADDON Bot Worker `PUBLIC_FEED_RELAY_KEY`
- Live Feed `ABADDON_FIVEM_BRIDGE_SECRET` = FiveM `server.cfg`의 `abaddon_bridge_secret`
- Bot `PUBLIC_FEED_RELAY_URL` = 실제 실행 중인 Live Feed 주소
- FiveM `abaddon_bridge_relay_url` = 위와 동일한 Live Feed 주소
- FiveM `abaddon_bridge_guild_id` = 실제 Discord 서버 ID

비밀키는 GitHub 파일에 커밋하지 말고 호스팅 서비스 환경변수에만 저장하세요.
