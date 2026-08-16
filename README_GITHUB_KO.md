# ABADDON Live Feed v1.7.0 · GitHub 배포용

이 ZIP은 저장소 **루트에 그대로 덮어쓰는** 형태입니다. `live_feed_server.py`, `requirements.txt`, `render.yaml`이 같은 루트에 있어야 합니다.

## 업데이트
1. 기존 Live Feed GitHub 저장소 백업/브랜치 생성
2. 이 ZIP 내용을 저장소 루트에 덮어쓰기
3. commit / push
4. 저장소와 연결된 Web Service의 자동 배포 완료 확인
5. `/health`에서 `version: 1.7.0` 확인
6. `/api/bridge/diagnostics`에서 `fivem_bridge_configured: true` 확인

## 반드시 맞아야 하는 값
- Live Feed `PUBLIC_FEED_RELAY_KEY` = ABADDON Bot Worker `PUBLIC_FEED_RELAY_KEY`
- Live Feed `ABADDON_FIVEM_BRIDGE_SECRET` = FiveM `server.cfg`의 `abaddon_bridge_secret`
- Bot `PUBLIC_FEED_RELAY_URL` = 실제 실행 중인 Live Feed 주소
- FiveM `abaddon_bridge_relay_url` = 위와 동일한 Live Feed 주소
- FiveM `abaddon_bridge_guild_id` = 실제 Discord 서버 ID

비밀키는 GitHub 파일에 커밋하지 말고 호스팅 서비스 환경변수에만 저장하세요.

## v1.7.0 / ABADDON OUTBREAK
- ABADDON LIFE v2.0.0의 `outbreak_*` 이벤트를 기존 FiveM 브리지로 수신합니다.
- `/api/fivem/outbreak?server_id=abaddon-life-01` 에서 최근 OUTBREAK 상태를 확인할 수 있습니다.
- 기존 `PUBLIC_FEED_RELAY_KEY`, `ABADDON_FIVEM_BRIDGE_SECRET` 값은 변경하지 않습니다.


## v1.7.0 / ABADDON LIFE v2.2.0
- OUTBREAK 보급 투하 / 구조 임무 / 정부 재난방송 / 특수 감염체 이벤트와 호환됩니다.
- 기존 ABADDON_FIVEM_BRIDGE_SECRET 및 PUBLIC_FEED_RELAY_KEY 값은 변경하지 않습니다.
- Atlas 지도 설치를 다시 할 필요가 없습니다.


## v1.8.0 / ABADDON LIFE v2.3.0
- OUTBREAK 자동 단계 상승 이벤트(outbreak_phase_auto) 호환.
- 기존 /api/fivem/outbreak 상태 저장 방식 그대로 사용.
- Life 2.3.0 / Outbreak 2.3.0 호환 버전 표기 갱신.


## v1.9.0 / ABADDON LIFE v2.4.0
- Horde/Finale/Scavenge/CITYFALL 이벤트 전달 호환.
- outbreak_horde / outbreak_horde_clear / outbreak_finale / outbreak_scavenge 이벤트 수용.
- LIFE / OUTBREAK 호환 버전 2.4.0 갱신.


## v1.9.1 / ABADDON LIFE v2.4.1
- OUTBREAK Spawn Director / Radar / integrated LIFE HUD 호환.
- 서버 이벤트 API 변경 없음.
- LIFE / OUTBREAK 호환 버전 2.4.1 갱신.


## v1.10.0 / LIFE v2.5.0 FINAL
- Friendly survivor / Raider / Contract / Reputation 이벤트 호환.
- Civilian outbreak / HUD toggle은 클라이언트 전용으로 API 변경 없음.
- LIFE / OUTBREAK 2.5.0 호환.


## v1.10.1 / LIFE v2.5.1
- Population Shift / civilian infection runtime compatibility.
- Chat layout and in-place civilian conversion are client-side; bridge API change 없음.
- LIFE / OUTBREAK compatibility 2.5.1.


## v1.10.2 / LIFE v2.5.2
- Infected Identity / custom attack AI compatibility.
- Visual/attack changes are client-side; bridge API changes 없음.
- LIFE / OUTBREAK compatibility 2.5.2.


## v1.10.3 / LIFE v2.5.3
- Infection treatment bridge event compatibility.
- AI/loot/admin-search/chat changes are local UI/gameplay; existing API remains compatible.
- LIFE / OUTBREAK compatibility 2.5.3.


## v1.10.4 / LIFE v2.5.6
- Duplicate join/fresh infection reset/godmode stability compatibility.
- Friendly UI, inventory quantity, R reload changes are local gameplay/UI; bridge schema change 없음.
- LIFE / OUTBREAK compatibility 2.5.6.


## v1.10.5 / LIFE v2.5.7
- OUTBREAK 재입장/UI 잔상 하드닝 호환.
- LIFE / OUTBREAK compatibility 2.5.7.
- Bot 19.6.3 / Website 5.1.3 호환 유지.
- API 스키마 및 환경변수 변경 없음.


## v1.11.0 / LIFE v2.6.0

- LIFE / OUTBREAK compatibility 2.6.0.
- 신규 `outbreak_horde_start`, `outbreak_field_mission`, `outbreak_field_complete`, `outbreak_escape_open`, `outbreak_escape_complete`, `outbreak_city_incident` 이벤트를 기존 `outbreak_*` 범용 수신 구조로 그대로 표시합니다.
- 대규모 활성 감염자 수, 시민 감염 전환, 장전/크로스헤어/아이템 버리기는 클라이언트 동작이므로 Live Feed API 스키마 변경 없음.
- Bot 19.6.3 / Website 5.1.3 호환 유지.


## v1.11.1 / LIFE v2.6.1
- OUTBREAK real melee hitbox hotfix compatibility.
- Event/API payload schema unchanged from v1.11.0.
- Bot 19.6.3 / Website 5.1.3 compatibility retained.


## v1.12.0 / LIFE v2.7.0
- CITY COLLAPSE 이벤트(outbreak_city_collapse) 수신/표시 호환.
- 차량 전투/자동 장전은 게임 내부 로직 변경이며 API 스키마 변경 없음.
- Bot v19.6.3 / Website v5.1.3 호환 유지.


## v1.12.1 / LIFE v2.7.1
- OUTBREAK combat-direct / special infected visual-detail hotfix compatibility.
- 무기 전환/발사율/특수 감염자 외형은 게임 클라이언트 로직 변경이며 Live Feed API 스키마 변경 없음.
- Bot v19.6.3 / Website v5.1.3 호환 유지.


## v1.12.2 / BOT v19.6.4
- ABADDON Bot v19.6.4 emergency-maintenance + command-guide hotfix compatibility.
- Website v5.1.4 current-version metadata compatibility.
- ABADDON LIFE / OUTBREAK v2.7.1 API/event contract unchanged.

## v1.12.3 / BOT v19.6.5
- ABADDON Bot v19.6.5 command usage logs + UI error watch compatibility.
- English Server Mirror feature requires no relay API change.
- Website v5.1.5 current-version metadata compatibility.
- ABADDON LIFE / OUTBREAK v2.7.1 compatibility retained.

## v1.12.4 / Website v5.1.6
- English Privacy Policy parity/hreflang website metadata compatibility.
- BOT v19.6.5 / LIFE v2.7.1 / OUTBREAK v2.7.1 API contract unchanged.

## v1.12.5 / LIFE v2.7.2
- 좀비모드 재입장 차단 / HUD 안정화 / 빈 총탄 인벤토리 자동 장전 하드닝 호환.
- LIFE / OUTBREAK compatibility 2.7.2.
- BOT v19.6.5 / Website v5.1.6 호환 유지.
- Live Feed API / 이벤트 payload / 환경변수 계약 변경 없음.

## v1.12.6 / LIFE v2.7.3
- LIFE / OUTBREAK compatibility 2.7.3.
- Safe-zone perimeter / interactions / admin item UI / vehicle reload fixes; relay API/event contract unchanged.
- BOT v19.6.5 / Website v5.1.6 compatibility retained.


## v1.13.2 / LIFE v2.8.2
- LIFE / OUTBREAK compatibility 2.8.2.
- 투명 HUD, 전투 잠금 복구, 탄창 재장전 핫픽스, 인벤토리/총기 파츠 UI 변경은 클라이언트 측이며 Relay API 계약 변경 없음.
- BOT v19.6.5 / Website v5.1.6 호환 유지.

## v1.13.3 / LIFE v2.8.3
- LIFE / OUTBREAK compatibility 2.8.3.
- 다단계 탈출 프로토콜의 신규 `outbreak_escape_prep`, `outbreak_escape_prep_complete` 이벤트를 기존 범용 브리지 계약으로 수신합니다.
- Relay API 계약 변경 없음. BOT v19.6.5 / Website v5.1.6 유지.


## v1.13.4 / LIFE v2.8.4
- LIFE / OUTBREAK compatibility 2.8.4.
- v2.8.4 native magazine reload hotfix metadata only; relay API contract unchanged.


## v1.13.5 / LIFE v2.8.5
- LIFE / OUTBREAK compatibility 2.8.5.
- 자동 탈출 퀘스트 GPS / 신규 시민 150·150 시작자금 / OUTBREAK 초보자 무기팩 호환 메타데이터.
- Relay API contract unchanged.


## v1.13.6 / LIFE v2.8.6
- LIFE / OUTBREAK compatibility 2.8.6.
- HUD/chat/nameplate/phone services/quick-slot/nearby-drop UI는 클라이언트 기능이라 기존 relay API 계약은 변경하지 않습니다.
- Korean fishing/life activities resource 추가와 호환 메타데이터를 갱신했습니다.


## v1.13.7 / LIFE v2.8.7
- LIFE / OUTBREAK compatibility 2.8.7.
- 생활 NPC 허브 / 현장 NPC / 아이템 카드 UI 패치와 호환 메타데이터 최신화.
- Bot v19.6.5 / Website v5.1.6 유지.


## v1.13.9 / LIFE v2.10.0
- LIFE / OUTBREAK compatibility 2.10.0.
- KRW economy rebalancing and seafood/life-activity expansion compatibility metadata updated.
- Relay protocol remains backward-compatible.

## v1.13.8 / LIFE v2.8.8
- LIFE / OUTBREAK compatibility 2.8.8.
- HUD/NPC/UI recovery patch compatibility metadata only; API contract unchanged.
