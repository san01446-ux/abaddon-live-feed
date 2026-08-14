from __future__ import annotations

import json
import os
import secrets
import threading
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Mapping, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

VERSION = "1.2.0"
MAX_EVENTS = 120
SESSION_TTL = 60 * 60 * 12
STATE_TTL = 10 * 60
ACTION_TTL = 90
ACTION_WAIT_SECONDS = 35

LOCK = threading.RLock()
EVENTS: list[dict[str, Any]] = []
STATUS: dict[str, Any] = {"ok": True, "online": False, "version": "unknown"}
WORKER_INDEX: dict[str, Any] = {"guilds": [], "version": "unknown", "online": False, "updated_at": 0}
SESSIONS: dict[str, dict[str, Any]] = {}
OAUTH_STATES: dict[str, dict[str, Any]] = {}
ACTIONS: dict[str, dict[str, Any]] = {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _allowed_origin() -> str:
    return str(os.getenv("PUBLIC_FEED_ALLOWED_ORIGIN", "*") or "*").strip() or "*"


def _relay_secret() -> str:
    return str(os.getenv("PUBLIC_FEED_RELAY_KEY", "") or os.getenv("ABADDON_FEED_SECRET", "") or "").strip()


def _site_url() -> str:
    return str(os.getenv("ABADDON_SITE_URL", "https://san01446-ux.github.io/abaddon-policy") or "").rstrip("/")


def _oauth_redirect_uri() -> str:
    value = str(os.getenv("DISCORD_OAUTH_REDIRECT_URI", "") or "").strip()
    if value:
        return value
    public = str(os.getenv("RENDER_EXTERNAL_URL", "") or "").rstrip("/")
    return f"{public}/auth/callback" if public else ""


def _now() -> int:
    return int(time.time())


def _cleanup() -> None:
    now = time.time()
    with LOCK:
        for key in list(SESSIONS):
            if float(SESSIONS[key].get("expires", 0)) <= now:
                SESSIONS.pop(key, None)
        for key in list(OAUTH_STATES):
            if float(OAUTH_STATES[key].get("created", 0)) + STATE_TTL <= now:
                OAUTH_STATES.pop(key, None)
        for key in list(ACTIONS):
            row = ACTIONS.get(key) or {}
            created = float(row.get("created", 0))
            done_at = float(row.get("done_at", 0))
            if done_at and done_at + 90 <= now:
                ACTIONS.pop(key, None)
            elif not done_at and created + ACTION_TTL * 3 <= now:
                ACTIONS.pop(key, None)


def _http_json(url: str, *, method: str = "GET", headers: Optional[Mapping[str, str]] = None, data: Optional[bytes] = None, timeout: int = 15) -> Any:
    req = urllib_request.Request(url, data=data, method=method, headers=dict(headers or {}))
    with urllib_request.urlopen(req, timeout=timeout) as response:
        raw = response.read(1_000_000).decode("utf-8", "replace")
        return json.loads(raw) if raw else {}


def _discord_oauth_exchange(code: str) -> dict[str, Any]:
    client_id = str(os.getenv("DISCORD_OAUTH_CLIENT_ID", "") or "").strip()
    secret = str(os.getenv("DISCORD_OAUTH_CLIENT_SECRET", "") or "").strip()
    redirect_uri = _oauth_redirect_uri()
    if not client_id or not secret or not redirect_uri:
        raise RuntimeError("oauth_not_configured")
    form = urllib_parse.urlencode({
        "client_id": client_id,
        "client_secret": secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }).encode("utf-8")
    token = _http_json(
        "https://discord.com/api/oauth2/token",
        method="POST",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": f"ABADDON-LiveFeed/{VERSION}"},
    )
    access = str(token.get("access_token") or "") if isinstance(token, Mapping) else ""
    if not access:
        raise RuntimeError("oauth_token_missing")
    auth = {"Authorization": f"Bearer {access}", "User-Agent": f"ABADDON-LiveFeed/{VERSION}"}
    profile = _http_json("https://discord.com/api/users/@me", headers=auth)
    guilds = _http_json("https://discord.com/api/users/@me/guilds", headers=auth)
    if not isinstance(profile, Mapping):
        raise RuntimeError("discord_profile_invalid")
    if not isinstance(guilds, list):
        guilds = []
    uid = str(profile.get("id") or "")
    if not uid:
        raise RuntimeError("discord_user_missing")
    avatar_hash = str(profile.get("avatar") or "")
    avatar = f"https://cdn.discordapp.com/avatars/{uid}/{avatar_hash}.png?size=128" if avatar_hash else ""
    safe_guilds = []
    for row in guilds[:200]:
        if not isinstance(row, Mapping):
            continue
        safe_guilds.append({
            "id": str(row.get("id") or ""),
            "name": str(row.get("name") or "")[:100],
            "permissions": str(row.get("permissions") or "0"),
            "owner": bool(row.get("owner")),
            "icon": str(row.get("icon") or "")[:120],
        })
    return {
        "user_id": uid,
        "username": str(profile.get("global_name") or profile.get("username") or "Discord user")[:80],
        "avatar": avatar,
        "guilds": safe_guilds,
    }


def _session_from_handler(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    value = str(handler.headers.get("Authorization") or "")
    if not value.lower().startswith("bearer "):
        return {}
    token = value[7:].strip()
    with LOCK:
        row = SESSIONS.get(token)
        return dict(row) if isinstance(row, dict) and float(row.get("expires", 0)) > time.time() else {}


def _can_manage(session: Mapping[str, Any], guild_id: str) -> bool:
    gid = str(guild_id or "")
    for row in session.get("guilds", []) if isinstance(session.get("guilds"), list) else []:
        if not isinstance(row, Mapping) or str(row.get("id")) != gid:
            continue
        permissions = _safe_int(row.get("permissions"), 0)
        return bool(row.get("owner") or (permissions & 0x8) or (permissions & 0x20))
    return False


def _worker_has_guild(guild_id: str) -> bool:
    with LOCK:
        rows = WORKER_INDEX.get("guilds") if isinstance(WORKER_INDEX.get("guilds"), list) else []
        return any(isinstance(row, Mapping) and str(row.get("id")) == str(guild_id) for row in rows)


def _worker_fresh() -> bool:
    with LOCK:
        updated = float(WORKER_INDEX.get("updated_at", 0) or 0)
        return bool(updated and time.time() - updated <= 90)


def _enqueue(op: str, *, user_id: str = "", guild_id: str = "", payload: Optional[Mapping[str, Any]] = None) -> tuple[str, threading.Event]:
    action_id = "act_" + secrets.token_urlsafe(18)
    event = threading.Event()
    with LOCK:
        ACTIONS[action_id] = {
            "id": action_id,
            "op": str(op),
            "user_id": str(user_id or ""),
            "guild_id": str(guild_id or ""),
            "payload": dict(payload or {}),
            "created": time.time(),
            "status": "queued",
            "lease_until": 0.0,
            "event": event,
            "result": None,
        }
    return action_id, event


def _await_action(action_id: str, event: threading.Event) -> dict[str, Any]:
    event.wait(ACTION_WAIT_SECONDS)
    with LOCK:
        row = ACTIONS.get(action_id) or {}
        result = row.get("result")
        if isinstance(result, dict):
            return dict(result)
        return {"ok": False, "error": "worker_timeout"}


def _dispatch(op: str, *, session: Optional[Mapping[str, Any]] = None, guild_id: str = "", payload: Optional[Mapping[str, Any]] = None, user_id: str = "") -> dict[str, Any]:
    if not _worker_fresh():
        return {"ok": False, "error": "worker_offline"}
    if session is not None:
        user_id = str(session.get("user_id") or "")
    action_id, event = _enqueue(op, user_id=user_id, guild_id=guild_id, payload=payload)
    return _await_action(action_id, event)


class Handler(BaseHTTPRequestHandler):
    server_version = f"ABADDONLiveFeed/{VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[live-feed] {self.address_string()} {fmt % args}", flush=True)

    def _cors(self) -> None:
        origin = _allowed_origin()
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        raw = json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self._cors()
        self.end_headers()
        self.wfile.write(raw)

    def _redirect(self, location: str, *, cookie: str = "") -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _body(self) -> dict[str, Any]:
        try:
            length = max(0, min(262144, _safe_int(self.headers.get("Content-Length"), 0)))
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8", "replace"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _worker_authorized(self) -> bool:
        secret = _relay_secret()
        value = str(self.headers.get("Authorization") or "")
        return bool(secret and value == f"Bearer {secret}")

    def _require_session(self) -> Optional[dict[str, Any]]:
        session = _session_from_handler(self)
        if not session:
            self._json(401, {"ok": False, "error": "login_required"})
            return None
        return session

    def _require_guild(self, session: Mapping[str, Any], guild_id: str) -> bool:
        if not guild_id or not _can_manage(session, guild_id):
            self._json(403, {"ok": False, "error": "guild_forbidden"})
            return False
        if not _worker_has_guild(guild_id):
            self._json(404, {"ok": False, "error": "guild_not_found"})
            return False
        return True

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urllib_parse.urlparse(self.path)
        if parsed.path in {"/", "/health", "/healthz"}:
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store, max-age=0")
            self._cors()
            self.end_headers()
            return
        self.send_response(404)
        self._cors()
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        _cleanup()
        parsed = urllib_parse.urlparse(self.path)
        path = parsed.path
        query = urllib_parse.parse_qs(parsed.query or "")

        if path in {"/", "/health", "/healthz"}:
            self._json(200, {"ok": True, "service": "ABADDON live-feed + dashboard relay", "version": VERSION, "worker_online": _worker_fresh()})
            return
        if path == "/api/status":
            with LOCK:
                payload = dict(STATUS)
                payload["relay_version"] = VERSION
                payload["worker_fresh"] = _worker_fresh()
            self._json(200, payload)
            return
        if path == "/api/events":
            limit = max(1, min(50, _safe_int((query.get("limit") or [10])[0], 10)))
            with LOCK:
                rows = [dict(row) for row in EVENTS[:limit]]
            self._json(200, {"ok": True, "events": rows, "version": VERSION})
            return
        if path == "/api/leaderboard":
            kind = str((query.get("type") or ["pvp"])[0]).lower()
            result = _dispatch("leaderboard_get", payload={"type": kind})
            self._json(200 if result.get("ok") else 503, result)
            return

        if path == "/auth/discord":
            client_id = str(os.getenv("DISCORD_OAUTH_CLIENT_ID", "") or "").strip()
            redirect_uri = _oauth_redirect_uri()
            if not client_id or not redirect_uri:
                self._json(503, {"ok": False, "error": "oauth_not_configured"})
                return
            lang = "en" if str((query.get("lang") or [""])[0]).lower() == "en" else "ko"
            state = secrets.token_urlsafe(24)
            with LOCK:
                OAUTH_STATES[state] = {"created": time.time(), "lang": lang}
            target = "https://discord.com/oauth2/authorize?" + urllib_parse.urlencode({
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "identify guilds",
                "state": state,
            })
            cookie = f"abaddon_oauth_state={state}; Max-Age={STATE_TTL}; Path=/; HttpOnly; SameSite=Lax; Secure"
            self._redirect(target, cookie=cookie)
            return

        if path == "/auth/callback":
            code = str((query.get("code") or [""])[0])
            state = str((query.get("state") or [""])[0])
            cookies = SimpleCookie()
            cookies.load(str(self.headers.get("Cookie") or ""))
            cookie_state = cookies.get("abaddon_oauth_state").value if cookies.get("abaddon_oauth_state") else ""
            with LOCK:
                info = dict(OAUTH_STATES.get(state, {})) if state else {}
                OAUTH_STATES.pop(state, None)
            valid = bool(state and state == cookie_state and info and float(info.get("created", 0)) + STATE_TTL > time.time())
            site = _site_url()
            page = "/en/dashboard.html" if str(info.get("lang") or "ko") == "en" else "/dashboard.html"
            if not valid or not code:
                self._redirect(f"{site}{page}?error=oauth_state")
                return
            try:
                discord_session = _discord_oauth_exchange(code)
                token = secrets.token_urlsafe(32)
                discord_session["expires"] = time.time() + SESSION_TTL
                with LOCK:
                    SESSIONS[token] = discord_session
                self._redirect(
                    f"{site}{page}#session={urllib_parse.quote(token)}",
                    cookie="abaddon_oauth_state=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax; Secure",
                )
            except Exception as exc:
                print(f"[oauth] callback error: {type(exc).__name__}: {exc}", flush=True)
                self._redirect(f"{site}{page}?error=oauth_exchange")
            return

        if path == "/auth/logout":
            value = str(self.headers.get("Authorization") or "")
            token = value[7:].strip() if value.lower().startswith("bearer ") else ""
            if token:
                with LOCK:
                    SESSIONS.pop(token, None)
            self._json(200, {"ok": True})
            return

        if path == "/api/me":
            session = self._require_session()
            if session is None:
                return
            result = _dispatch("profile_get", session=session, payload={"user_id": str(session.get("user_id") or "")})
            if not result.get("ok"):
                self._json(503 if result.get("error") in {"worker_offline", "worker_timeout"} else 400, result)
                return
            result["discord"] = {k: session.get(k) for k in ("user_id", "username", "avatar")}
            self._json(200, result)
            return

        if path == "/api/dashboard/guilds":
            session = self._require_session()
            if session is None:
                return
            with LOCK:
                worker_rows = WORKER_INDEX.get("guilds") if isinstance(WORKER_INDEX.get("guilds"), list) else []
                rows = [dict(row) for row in worker_rows if isinstance(row, Mapping) and _can_manage(session, str(row.get("id") or ""))]
                version = str(WORKER_INDEX.get("version") or "unknown")
            self._json(200, {"ok": True, "guilds": rows, "version": version, "worker_fresh": _worker_fresh()})
            return

        get_map = {
            "/api/dashboard/settings": "settings_get",
            "/api/dashboard/structure": "structure_get",
            "/api/dashboard/overview": "overview_get",
            "/api/dashboard/reactions": "reactions_get",
            "/api/dashboard/external": "external_get",
            "/api/dashboard/commands": "commands_get",
        }
        if path in get_map:
            session = self._require_session()
            if session is None:
                return
            guild_id = str((query.get("guild_id") or [""])[0])
            if not self._require_guild(session, guild_id):
                return
            result = _dispatch(get_map[path], session=session, guild_id=guild_id, payload={"guild_id": guild_id})
            self._json(200 if result.get("ok") else 503, result)
            return

        if path == "/api/control/pull":
            if not self._worker_authorized():
                self._json(401, {"ok": False, "error": "relay_unauthorized"})
                return
            limit = max(1, min(50, _safe_int((query.get("limit") or [25])[0], 25)))
            now = time.time()
            rows: list[dict[str, Any]] = []
            with LOCK:
                for action in ACTIONS.values():
                    if len(rows) >= limit:
                        break
                    status = str(action.get("status") or "queued")
                    lease_until = float(action.get("lease_until", 0) or 0)
                    if status == "done":
                        continue
                    if status == "leased" and lease_until > now:
                        continue
                    action["status"] = "leased"
                    action["lease_until"] = now + 60
                    rows.append({k: action.get(k) for k in ("id", "op", "user_id", "guild_id", "payload")})
            self._json(200, {"ok": True, "actions": rows, "version": VERSION})
            return

        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        _cleanup()
        parsed = urllib_parse.urlparse(self.path)
        path = parsed.path
        body = self._body()

        if path == "/api/ingest/event":
            if not self._worker_authorized():
                self._json(401, {"ok": False, "error": "relay_unauthorized"})
                return
            row = dict(body)
            with LOCK:
                EVENTS.insert(0, row)
                del EVENTS[MAX_EVENTS:]
            self._json(200, {"ok": True, "stored": True})
            return

        if path == "/api/ingest/status":
            if not self._worker_authorized():
                self._json(401, {"ok": False, "error": "relay_unauthorized"})
                return
            with LOCK:
                STATUS.clear()
                STATUS.update(dict(body))
                STATUS["ok"] = True
                STATUS["received_at"] = _now()
            self._json(200, {"ok": True})
            return

        if path == "/api/worker/index":
            if not self._worker_authorized():
                self._json(401, {"ok": False, "error": "relay_unauthorized"})
                return
            guilds = body.get("guilds") if isinstance(body.get("guilds"), list) else []
            safe = []
            for row in guilds[:500]:
                if not isinstance(row, Mapping):
                    continue
                safe.append({
                    "id": str(row.get("id") or ""),
                    "name": str(row.get("name") or "")[:100],
                    "members": max(0, _safe_int(row.get("members"), 0)),
                    "icon": str(row.get("icon") or "")[:500],
                })
            with LOCK:
                WORKER_INDEX.clear()
                WORKER_INDEX.update({
                    "guilds": safe,
                    "version": str(body.get("version") or "unknown")[:40],
                    "online": bool(body.get("online")),
                    "updated_at": time.time(),
                })
            self._json(200, {"ok": True, "guilds": len(safe), "version": VERSION})
            return

        if path == "/api/control/result":
            if not self._worker_authorized():
                self._json(401, {"ok": False, "error": "relay_unauthorized"})
                return
            action_id = str(body.get("id") or "")
            result = body.get("result") if isinstance(body.get("result"), dict) else {"ok": False, "error": "invalid_worker_result"}
            with LOCK:
                row = ACTIONS.get(action_id)
                if row is None:
                    self._json(404, {"ok": False, "error": "action_not_found"})
                    return
                row["status"] = "done"
                row["result"] = dict(result)
                row["done_at"] = time.time()
                event = row.get("event")
                if isinstance(event, threading.Event):
                    event.set()
            self._json(200, {"ok": True})
            return

        post_map = {
            "/api/dashboard/settings": "settings_set",
            "/api/dashboard/reactions": "reactions_set",
            "/api/dashboard/external/youtube": "external_youtube_add",
            "/api/dashboard/external/twitch": "external_twitch_add",
            "/api/dashboard/external/remove": "external_remove",
        }
        if path in post_map:
            session = self._require_session()
            if session is None:
                return
            guild_id = str(body.get("guild_id") or "")
            if not self._require_guild(session, guild_id):
                return
            result = _dispatch(post_map[path], session=session, guild_id=guild_id, payload=body)
            status = 200 if result.get("ok") else (503 if result.get("error") in {"worker_offline", "worker_timeout"} else 400)
            self._json(status, result)
            return

        self._json(404, {"ok": False, "error": "not_found"})


def main() -> None:
    port = max(1, min(65535, _safe_int(os.getenv("PORT") or 10000, 10000)))
    print(f"[ABADDON live-feed v{VERSION}] starting on 0.0.0.0:{port}", flush=True)
    print(f"[ABADDON live-feed] OAuth redirect: {_oauth_redirect_uri() or 'NOT CONFIGURED'}", flush=True)
    print(f"[ABADDON live-feed] Relay secret: {'configured' if _relay_secret() else 'MISSING'}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
