# Slack Relay Stabilization Plan

**Author:** Ops Agent  
**Date:** 2025-01-27  
**Target:** `scripts/slack_bot.py`

---

## 1. Current Issues Found

### 1.1 No Socket Mode Reconnection Handling

The bot starts `SocketModeHandler.start()` as a blocking call with **zero reconnection logic**. If the WebSocket drops (network blip, Slack maintenance, token rotation), the process either hangs or exits silently.

```python
# Current - no retry, no reconnect wrapper
handler = SocketModeHandler(app, APP_TOKEN)
handler.start()  # blocks forever or dies silently
```

**Impact:** Bot goes offline with no alert and no auto-recovery. Must be manually restarted.

### 1.2 No Health Check in Socket Mode

HTTP mode has a `/health` endpoint. Socket mode has **nothing** - no heartbeat, no liveness probe, no way for an external monitor to know the bot is alive.

### 1.3 Unhandled Event Types Cause Silent Failures

Only `app_mention`, `message`, and `/claw` are registered. Any other event Slack sends (e.g. `member_joined_channel`, `reaction_added`, `app_home_opened`, `tokens_revoked`) hits slack-bolt default handler and is silently dropped.
### 1.4 File-Based Logging is Fragile

`log_line()` reads the entire file, appends, and writes it back on every single message. It uses `read_text() + append + write_text()` which is:

- **Race-prone:** Multiple threads (main event loop + `queue_tick`) can corrupt the file.
- **O(n) per write:** Reads the entire log on every call. Degrades after 10K+ messages.
- **No rotation:** File grows unbounded.
- Same anti-pattern in `log_anthropic_usage()` and codex usage logging.

### 1.5 Relay HTTP Calls Swallow All Errors

`relay_post()` catches all exceptions and returns `None` with **no logging**. If the relay service is down, every message silently loses context. No alert, no metric, no log.

### 1.6 Messages Can Be Dropped

- **Relay context fetch fails silently** - Codex runs without conversation history.
- **`should_send_reply()` duplicate suppression** uses an in-memory dict with no TTL cleanup. `_LAST_REPLY` grows unbounded over days.
- **`chat_postMessage` failures** are caught but not retried - message is lost.
- **Slack API rate limiting** (`ratelimited` error) is not handled - reply is dropped.

### 1.7 In-Memory State is Not Persisted

All pending approvals, code jobs, and exec jobs live in plain dicts (`_PENDING_APPROVALS`, `_PENDING_CODE`, `_PENDING_EXEC`). A process restart loses all pending approval cards.

### 1.8 `queue_tick` Thread Has No Restart Logic

If the daemon thread dies, there is no supervisor to restart it. The full `QUEUE_INTERVAL` sleep runs even after errors.

### 1.9 No Graceful Shutdown

No signal handler. No cleanup of in-flight messages. `SocketModeHandler.start()` blocks and Ctrl+C may leave zombie WebSocket connections.
---

## 2. Recommended Fixes

### 2.1 Socket Mode Reconnection Wrapper

Replace the bare `handler.start()` with an exponential-backoff reconnection loop:

```python
import random

MAX_RECONNECT_DELAY = 300  # 5 minutes
INITIAL_RECONNECT_DELAY = 5

def run_socket_mode_with_reconnect():
    delay = INITIAL_RECONNECT_DELAY
    consecutive_failures = 0

    while True:
        try:
            log_line(f"socket mode connecting (failures={consecutive_failures})")
            handler = SocketModeHandler(app, APP_TOKEN)
            handler.connect()
            consecutive_failures = 0
            delay = INITIAL_RECONNECT_DELAY
            log_line("socket mode connected")

            while handler.client.is_connected():
                time.sleep(5)

            log_line("socket mode disconnected, will reconnect")
        except KeyboardInterrupt:
            log_line("shutdown requested")
            try:
                handler.close()
            except Exception:
                pass
            break
        except Exception as exc:
            consecutive_failures += 1
            log_line(f"socket mode error #{consecutive_failures}: {exc}")

        jitter = random.uniform(0, delay * 0.3)
        sleep_time = min(delay + jitter, MAX_RECONNECT_DELAY)
        log_line(f"reconnecting in {sleep_time:.1f}s")
        time.sleep(sleep_time)
        delay = min(delay * 2, MAX_RECONNECT_DELAY)
```

Replace the `__main__` socket mode block with:

```python
else:
    run_socket_mode_with_reconnect()
```
### 2.2 Health Check for Socket Mode

Add a lightweight HTTP health server on a background thread:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

_LAST_EVENT_TS = time.time()
_BOOT_TS = time.time()
HEALTH_PORT = int(os.environ.get("CLAWDBOT_HEALTH_PORT", "8093"))

def update_health_ts():
    global _LAST_EVENT_TS
    _LAST_EVENT_TS = time.time()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        now = time.time()
        healthy = (now - _LAST_EVENT_TS) < 600
        body = json.dumps({
            "status": "ok" if healthy else "stale",
            "uptime_s": int(now - _BOOT_TS),
            "last_event_ago_s": int(now - _LAST_EVENT_TS),
            "paused": _AGENT_PAUSED,
            "pending_approvals": len(_PENDING_APPROVALS),
            "pending_exec": len(_PENDING_EXEC),
        })
        self.send_response(200 if healthy else 503)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass

def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log_line(f"health server on :{HEALTH_PORT}")
```

Call `update_health_ts()` at the top of `on_message`, `on_app_mention`, and `on_slash_claw`.
### 2.3 Catch-All Event Handlers

Register handlers for known noisy events to prevent Slack retries:

```python
@app.event("member_joined_channel")
def handle_member_joined(event):
    update_health_ts()

@app.event("reaction_added")
def handle_reaction(event):
    update_health_ts()

@app.event("app_home_opened")
def handle_app_home(event):
    update_health_ts()

@app.event("tokens_revoked")
def handle_tokens_revoked(event, logger):
    logger.critical("tokens_revoked event - bot may lose access")
    update_health_ts()
```

### 2.4 Fix File-Based Logging

Replace `log_line()` and usage loggers with `RotatingFileHandler`:

```python
from logging.handlers import RotatingFileHandler

slack_logger = logging.getLogger("clawdbot.slack")
_slack_handler = RotatingFileHandler(
    LOG_DIR / "clawdbot_slack.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
)
_slack_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
slack_logger.addHandler(_slack_handler)
slack_logger.setLevel(logging.INFO)

def log_line(message: str):
    """Thread-safe, append-only, rotating log."""
    slack_logger.info(message)
```

Apply the same pattern for `log_anthropic_usage()` and codex usage logging.
### 2.5 Add Relay Error Logging and Retry

```python
_RELAY_FAIL_COUNT = 0

def relay_post(path: str, payload: dict, timeout: int = 6, retries: int = 2):
    global _RELAY_FAIL_COUNT
    if not RELAY_URL:
        return None

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            data = json.dumps(payload).encode("utf-8")
            req = Request(
                f"{RELAY_URL}{path}",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=timeout) as resp:
                _RELAY_FAIL_COUNT = 0
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(0.5 * attempt)

    _RELAY_FAIL_COUNT += 1
    log_line(f"relay_post {path} failed x{retries}: {last_exc} (total: {_RELAY_FAIL_COUNT})")
    return None
```

### 2.6 Rate Limit Handling and Reply Retry

```python
def safe_post_message(channel: str, text: str, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            app.client.chat_postMessage(channel=channel, text=text)
            return True
        except SlackApiError as exc:
            if exc.response.get("error") == "ratelimited":
                wait = int(exc.response.headers.get("Retry-After", 5))
                log_line(f"rate limited, retry in {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                log_line(f"chat_postMessage error: {exc.response.get('error')}")
                return False
        except Exception as exc:
            log_line(f"chat_postMessage exception: {exc}")
            return False
    return False
```

Replace all `app.client.chat_postMessage(...)` in event handlers with `safe_post_message(...)`.
### 2.7 Periodic Cleanup of In-Memory State

```python
def cleanup_stale_state():
    while True:
        try:
            now = time.time()
            stale = [k for k, (_, ts) in _LAST_REPLY.items() if now - ts > 300]
            for k in stale:
                _LAST_REPLY.pop(k, None)
            if stale:
                log_line(f"cleanup: purged {len(stale)} stale reply entries")
        except Exception as exc:
            log_line(f"cleanup error: {exc}")
        time.sleep(300)
```

Start as daemon thread alongside `queue_tick`.

### 2.8 Persist Pending Approvals to Disk

```python
PENDING_STATE_PATH = LOG_DIR / "pending_state.json"

def _save_pending_state():
    state = {
        "approvals": _PENDING_APPROVALS,
        "exec": _PENDING_EXEC,
        "exec_status": _EXEC_STATUS,
        "code": dict(_PENDING_CODE_BY_JOB),
        "code_status": _CODE_STATUS,
        "saved_at": datetime.utcnow().isoformat(),
    }
    tmp = PENDING_STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(PENDING_STATE_PATH)

def _load_pending_state():
    if not PENDING_STATE_PATH.exists():
        return
    try:
        state = json.loads(PENDING_STATE_PATH.read_text())
        _PENDING_APPROVALS.update(state.get("approvals", {}))
        _PENDING_EXEC.update(state.get("exec", {}))
        _EXEC_STATUS.update(state.get("exec_status", {}))
        _PENDING_CODE_BY_JOB.update(state.get("code", {}))
        _CODE_STATUS.update(state.get("code_status", {}))
        log_line(f"restored {len(_PENDING_APPROVALS)} approvals, {len(_PENDING_EXEC)} exec")
    except Exception as exc:
        log_line(f"failed to restore pending state: {exc}")
```

Call `_load_pending_state()` at startup. Call `_save_pending_state()` after every approval/exec mutation.

### 2.9 Graceful Shutdown

```python
_shutdown_event = threading.Event()

def _signal_handler(signum, frame):
    log_line(f"signal {signum}, shutting down")
    _save_pending_state()
    _shutdown_event.set()

import signal
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
```

In the reconnection loop, check `_shutdown_event.is_set()` to break cleanly.
---

## 3. Health Monitoring Approach

### 3.1 Internal Health Server

- Socket mode: HTTP server on port 8093 (configurable via CLAWDBOT_HEALTH_PORT).
- HTTP mode: existing /health endpoint already present.
- Response includes: uptime, seconds since last event, paused state, pending job counts.
- Returns HTTP 503 if no events received in 10 minutes (stale detection).

### 3.2 External Health Check Script

Create scripts/check_slack_health.py:

```python
import json, sys, urllib.request

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8093"
try:
    resp = urllib.request.urlopen(url, timeout=5)
    data = json.loads(resp.read())
    if data.get("status") != "ok":
        print(f"WARN: stale")
        sys.exit(1)
    print("OK")
except Exception as e:
    print(f"CRIT: {e}")
    sys.exit(2)
```

### 3.3 Watchdog Integration

For Windows, use a scheduled task that runs check_slack_health.py every 5 minutes and restarts the bot if exit code >= 2.

### 3.4 Slack Channel Heartbeat

Post a heartbeat to a monitoring channel every 15 minutes with uptime and pending counts. Use the CLAWDBOT_HEARTBEAT_CHANNEL and CLAWDBOT_HEARTBEAT_INTERVAL env vars.
---

## 4. Testing Plan

### 4.1 Unit Tests

| Test | What it validates |
|------|-------------------|
| test_relay_post_retry | relay_post() retries on failure, logs after exhaustion |
| test_relay_post_success_resets | Failure counter resets on success |
| test_safe_post_ratelimit | safe_post_message() backs off on 429, retries |
| test_log_line_thread_safety | Multiple threads writing log_line() - no corruption |
| test_reply_cleanup | _LAST_REPLY entries purged after TTL |
| test_state_persist_restore | Save state, restart, verify approvals survive |
| test_kill_switch | Kill switch pauses, resume resumes |
| test_health_stale | Health returns 503 when _LAST_EVENT_TS is old |

### 4.2 Integration Tests

| Test | Steps |
|------|-------|
| Reconnection | Start bot, kill WebSocket, verify reconnects within 30s, verify messages resume |
| Relay down | Stop relay, send messages, verify bot responds (without context), verify errors logged |
| Rate limit | Mock Slack API 429, verify retry and eventual delivery |
| State persistence | Send approval, kill bot, restart, click Approve, verify resolves |
| Health probe | Start bot, curl :8093, verify JSON, wait 11 min, verify 503 |

### 4.3 Chaos / Soak Test

1. Run the bot 24+ hours under synthetic load (10 msg/min).
2. Periodically kill and restart the process.
3. Verify:
   - No messages dropped (compare sent vs received in relay log).
   - Log files rotate, stay under 15 MB.
   - _LAST_REPLY stays bounded (< 1000 entries).
   - Memory usage stays flat.

### 4.4 Acceptance Criteria

- [ ] Bot auto-reconnects within 60s of a WebSocket drop.
- [ ] Health endpoint returns JSON with uptime and staleness.
- [ ] Relay failures are logged with failure count.
- [ ] Slack rate limits are retried with Retry-After header.
- [ ] Pending approvals survive a process restart.
- [ ] Log files rotate at 5 MB, max 3 backups.
- [ ] No silent exception swallowing - every catch block logs.
- [ ] _LAST_REPLY is bounded by periodic cleanup.
---

## 5. Implementation Priority

| Priority | Fix | Effort |
|----------|-----|--------|
| P0 | Reconnection wrapper (2.1) | 1 hour |
| P0 | Fix file logging (2.4) | 30 min |
| P0 | Relay error logging (2.5) | 30 min |
| P1 | Health check server (2.2) | 1 hour |
| P1 | Rate limit retry (2.6) | 30 min |
| P1 | Graceful shutdown (2.9) | 30 min |
| P2 | State persistence (2.8) | 1 hour |
| P2 | Catch-all events (2.3) | 15 min |
| P2 | Memory cleanup (2.7) | 30 min |
