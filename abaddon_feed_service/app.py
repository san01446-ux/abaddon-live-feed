from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

VERSION = "4.3.2.1"
MAX_EVENTS = max(20, min(500, int(os.getenv("FEED_MAX_EVENTS", "100") or 100)))
MAX_BODY_BYTES = 16 * 1024
OFFLINE_AFTER_SECONDS = max(60, min(900, int(os.getenv("FEED_OFFLINE_AFTER_SECONDS", "150") or 150)))
STARTED_AT = time.time()
STATE_LOCK = threading.RLock()

EVENT_TYPES = {"enhance", "announcement", "system"}
METADATA_KEYS = {"item", "level", "tier", "protected", "version"}


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = text.replace("@everyone", "everyone").replace("@here", "here")
    return text[:limit]


def safe_int(value: Any, default: int = 0, minimum: int = 0, maximum: int = 10_000_000) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def parse_time(value: Any) -> float:
    text = clean_text(value, 64)
    if not text:
        return 0.0
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def sanitize_metadata(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: Dict[str, Any] = {}
    for key in METADATA_KEYS:
        if key not in value:
            continue
        item = value[key]
        if isinstance(item, bool):
            result[key] = item
        elif isinstance(item, int):
            result[key] = max(-1_000_000, min(1_000_000, item))
        elif isinstance(item, (float, str)):
            result[key] = clean_text(item, 80)
    return result


def sanitize_event(payload: Any) -> Dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    event_type = clean_text(source.get("type"), 24)
    if event_type not in EVENT_TYPES:
        event_type = "system"
    event_id = clean_text(source.get("id"), 72) or f"relay-{int(time.time() * 1000)}-{secrets.token_hex(4)}"
    created_at = clean_text(source.get("created_at"), 48)
    if not parse_time(created_at):
        created_at = utc_iso()
    accent = clean_text(source.get("accent"), 16)
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        accent = {"enhance": "#d6b45f", "announcement": "#a51f36", "system": "#7c6ee6"}[event_type]
    return {
        "id": event_id,
        "type": event_type,
        "title": clean_text(source.get("title"), 80) or "ABADDON 기록",
        "message": clean_text(source.get("message"), 220),
        "actor": clean_text(source.get("actor"), 48),
        "guild": clean_text(source.get("guild"), 48),
        "accent": accent,
        "created_at": created_at,
        "metadata": sanitize_metadata(source.get("metadata")),
    }


def sanitize_status(payload: Any) -> Dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    heartbeat_at = clean_text(source.get("heartbeat_at") or source.get("generated_at"), 48)
    if not parse_time(heartbeat_at):
        heartbeat_at = utc_iso()
    return {
        "online": bool(source.get("online")),
        "version": clean_text(source.get("version"), 24) or f"v{VERSION}",
        "bot": clean_text(source.get("bot"), 48) or "ABADDON",
        "guilds": safe_int(source.get("guilds"), 0, 0, 100_000),
        "members": safe_int(source.get("members"), 0, 0, 100_000_000),
        "latency_ms": safe_int(source.get("latency_ms"), 0, 0, 600_000),
        "feed_enabled": bool(source.get("feed_enabled", True)),
        "event_count": safe_int(source.get("event_count"), 0, 0, 1_000_000),
        "last_event_at": clean_text(source.get("last_event_at"), 48) or None,
        "heartbeat_at": heartbeat_at,
        "received_at": utc_iso(),
    }


def _data_path() -> Optional[Path]:
    value = os.getenv("FEED_DATA_FILE", "").strip()
    return Path(value) if value else None


STATE: Dict[str, Any] = {
    "events": [],
    "status": sanitize_status({"online": False, "version": f"v{VERSION}"}),
}


def load_state() -> None:
    path = _data_path()
    if path is None or not path.exists():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict):
        return
    events = raw.get("events")
    if isinstance(events, list):
        STATE["events"] = [sanitize_event(item) for item in events[:MAX_EVENTS] if isinstance(item, dict)]


def save_state() -> None:
    path = _data_path()
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps({"events": STATE["events"]}, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, path)
    except OSError as exc:
        print(f"[ABADDON FEED] persistence warning: {exc}", flush=True)


def allowed_origins() -> List[str]:
    raw = os.getenv("PUBLIC_FEED_ALLOWED_ORIGIN", "*").strip() or "*"
    return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]


def choose_cors_origin(request_origin: str) -> Optional[str]:
    origins = allowed_origins()
    if "*" in origins:
        return "*"
    normalized = request_origin.strip().rstrip("/")
    if normalized and normalized in origins:
        return normalized
    return None


def configured_secret() -> str:
    return os.getenv("ABADDON_FEED_SECRET", "").strip()


def is_authorized(headers: Any) -> bool:
    secret = configured_secret()
    if len(secret) < 24:
        return False
    authorization = str(headers.get("Authorization", ""))
    bearer = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    alternate = str(headers.get("X-ABADDON-FEED-KEY", "")).strip()
    provided = bearer or alternate
    return bool(provided) and secrets.compare_digest(provided, secret)


def public_status() -> Dict[str, Any]:
    with STATE_LOCK:
        status = dict(STATE.get("status") or {})
        event_count = len(STATE.get("events") or [])
    heartbeat_ts = parse_time(status.get("received_at") or status.get("heartbeat_at"))
    heartbeat_age = max(0, int(time.time() - heartbeat_ts)) if heartbeat_ts else 999_999
    online = bool(status.get("online")) and heartbeat_age <= OFFLINE_AFTER_SECONDS
    return {
        "ok": True,
        "online": online,
        "version": status.get("version") or f"v{VERSION}",
        "bot": status.get("bot") or "ABADDON",
        "guilds": safe_int(status.get("guilds")),
        "members": safe_int(status.get("members")),
        "latency_ms": safe_int(status.get("latency_ms")),
        "feed_enabled": bool(status.get("feed_enabled", True)),
        "event_count": event_count,
        "last_event_at": status.get("last_event_at"),
        "heartbeat_age_seconds": heartbeat_age,
        "relay_version": f"v{VERSION}",
        "uptime_seconds": max(0, int(time.time() - STARTED_AT)),
        "generated_at": utc_iso(),
    }


class FeedHandler(BaseHTTPRequestHandler):
    server_version = f"ABADDONRelay/{VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[ABADDON FEED] {self.address_string()} {fmt % args}", flush=True)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        cors = choose_cors_origin(str(self.headers.get("Origin", "")))
        if cors:
            self.send_header("Access-Control-Allow-Origin", cors)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-ABADDON-FEED-KEY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        length = safe_int(self.headers.get("Content-Length"), 0, 0, MAX_BODY_BYTES + 1)
        if length <= 0:
            return None, "empty_body"
        if length > MAX_BODY_BYTES:
            return None, "body_too_large"
        try:
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, "invalid_json"
        if not isinstance(data, dict):
            return None, "json_object_required"
        return data, None

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(204, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/health", "/healthz"}:
            self._send_json(200, {
                "ok": True,
                "service": "ABADDON public live-feed relay",
                "version": f"v{VERSION}",
                "secret_configured": len(configured_secret()) >= 24,
                "generated_at": utc_iso(),
            })
            return
        if parsed.path == "/api/status":
            self._send_json(200, public_status())
            return
        if parsed.path == "/api/events":
            query = parse_qs(parsed.query)
            limit = safe_int((query.get("limit") or [10])[0], 10, 1, 50)
            with STATE_LOCK:
                events = [dict(item) for item in STATE.get("events", [])[:limit] if isinstance(item, dict)]
                feed_enabled = bool((STATE.get("status") or {}).get("feed_enabled", True))
            self._send_json(200, {
                "ok": True,
                "version": f"v{VERSION}",
                "feed_enabled": feed_enabled,
                "events": events,
                "generated_at": utc_iso(),
            })
            return
        self._send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/ingest/event", "/api/ingest/status"}:
            self._send_json(404, {"ok": False, "error": "not_found"})
            return
        if len(configured_secret()) < 24:
            self._send_json(503, {"ok": False, "error": "ABADDON_FEED_SECRET_not_configured"})
            return
        if not is_authorized(self.headers):
            self._send_json(401, {"ok": False, "error": "unauthorized"})
            return
        payload, error = self._read_json()
        if error:
            self._send_json(400, {"ok": False, "error": error})
            return
        assert payload is not None

        if parsed.path == "/api/ingest/event":
            event = sanitize_event(payload)
            with STATE_LOCK:
                events: List[Dict[str, Any]] = STATE.setdefault("events", [])
                events[:] = [item for item in events if item.get("id") != event["id"]]
                events.insert(0, event)
                del events[MAX_EVENTS:]
                status = STATE.setdefault("status", {})
                status["last_event_at"] = event["created_at"]
            save_state()
            self._send_json(202, {"ok": True, "accepted": "event", "id": event["id"], "event_count": len(STATE["events"])})
            return

        status = sanitize_status(payload)
        with STATE_LOCK:
            STATE["status"] = status
        self._send_json(202, {"ok": True, "accepted": "status", "received_at": status["received_at"]})


def main() -> None:
    load_state()
    port = safe_int(os.getenv("PORT") or 10000, 10000, 1, 65535)
    if len(configured_secret()) < 24:
        print("[ABADDON FEED] WARNING: ABADDON_FEED_SECRET is missing or shorter than 24 characters. Ingest endpoints will reject requests.", flush=True)
    print(f"[ABADDON FEED] v{VERSION} listening on 0.0.0.0:{port}", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), FeedHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
