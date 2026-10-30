import asyncio
import json
import logging
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

from api.agent import agent_service
from api.config import BOT_TOKEN, KAKAO_GW_URL
from api.kakao_client import kakao_client

log = logging.getLogger("api.gateway")

# ── Opcodes ──────────────────────────────────────────────────────────
OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_READY = 3
OP_RESUME = 6
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11

# ── Close Codes ──────────────────────────────────────────────────────
CLOSE_SERVER_RESTART = 1001   # Graceful shutdown -> RESUME
CLOSE_AUTH_FAILED = 4001      # token 오류 -> 중단
CLOSE_INVALID_PAYLOAD = 4003  # 프로토콜 버그 -> 중단
CLOSE_REPLACED = 4004         # 중복 연결로 대체됨 -> 중단
CLOSE_SESSION_TIMEOUT = 4009  # 세션 만료 -> 새 IDENTIFY

RECONNECT_BACKOFF_SEC = 3.0


class GatewaySession:
    """카카오 봇 게이트웨이 WebSocket 세션 상태"""

    def __init__(self) -> None:
        self.session_id: str | None = None
        self.last_seq: int = 0
        self.connected: bool = False
        self.bot_id: str | None = None

    def can_resume(self) -> bool:
        return self.session_id is not None

    def reset(self) -> None:
        self.session_id = None
        self.last_seq = 0
        self.connected = False


gateway_session = GatewaySession()


async def handle_message_create(event_data: dict[str, Any]) -> None:
    """
    MESSAGE_CREATE 이벤트를 수신하면 AgentService를 통해 응답을 생성하고
    카카오 메시지 콜백 API(/v1/bot/callback)로 응답을 전송합니다.
    """
    content = event_data.get("content", "")
    callback_token = event_data.get("callbackToken", "")
    log.info("MESSAGE_CREATE 수신 — content=%r", content[:100])

    if not callback_token:
        log.error("callbackToken 누락 — 응답 전송 생략")
        return

    skill_response = await agent_service.generate_reply(content, context=event_data)
    try:
        result = await kakao_client.send_callback(callback_token, skill_response)
        log.info(
            "Callback 응답 발송 완료 — total=%d, send=%d, error=%d",
            result.totalCount,
            result.sendCount,
            result.errorCount,
        )
    except Exception as exc:
        log.exception("Callback 발송 실패: %s", exc)


async def _heartbeat(ws: Any, interval: float) -> None:
    while True:
        await asyncio.sleep(interval)
        await ws.send(json.dumps({"op": OP_HEARTBEAT}))


async def _receive(ws: Any, session: GatewaySession) -> None:
    async for raw in ws:
        payload = json.loads(raw)
        if payload.get("s") is not None:
            session.last_seq = payload["s"]
        if payload.get("op") == OP_DISPATCH and payload.get("t") == "MESSAGE_CREATE":
            asyncio.create_task(handle_message_create(payload["d"]))


async def _gateway_once(session: GatewaySession) -> None:
    log.info("Connecting to Kakao Bot Gateway: %s", KAKAO_GW_URL)
    async with websockets.connect(KAKAO_GW_URL) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000.0

        if session.can_resume():
            log.info("RESUME — session=%s, seq=%d", session.session_id, session.last_seq)
            await ws.send(
                json.dumps(
                    {
                        "op": OP_RESUME,
                        "d": {
                            "token": BOT_TOKEN,
                            "session_id": session.session_id,
                            "seq": session.last_seq,
                        },
                    }
                )
            )
            session.connected = True
        else:
            await ws.send(
                json.dumps(
                    {
                        "op": OP_IDENTIFY,
                        "d": {"token": BOT_TOKEN},
                    }
                )
            )
            ready = json.loads(await ws.recv())
            session.session_id = ready["d"]["session_id"]
            session.bot_id = ready["d"]["bot"]["id"]
            session.last_seq = 0
            session.connected = True
            log.info("READY — bot_id=%s, session=%s", session.bot_id, session.session_id)

        await asyncio.gather(
            _heartbeat(ws, heartbeat_interval),
            _receive(ws, session),
        )


def _should_resume(code: int | None) -> bool:
    if code in (CLOSE_AUTH_FAILED, CLOSE_INVALID_PAYLOAD, CLOSE_REPLACED):
        log.error("Gateway closed with code %s — 재연결 중단", code)
        return False
    if code == CLOSE_SESSION_TIMEOUT:
        return False
    return True


async def run_gateway_forever(session: GatewaySession = gateway_session) -> None:
    """백그라운드에서 게이트웨이 WebSocket 연결을 유지합니다."""
    if not BOT_TOKEN:
        log.warning("BOT_TOKEN이 설정되지 않아 게이트웨이 연결을 건너뜁니다.")
        return

    while True:
        try:
            await _gateway_once(session)
        except asyncio.CancelledError:
            session.connected = False
            log.info("Gateway task cancelled — 종료합니다.")
            raise
        except ConnectionClosed as exc:
            session.connected = False
            code = exc.rcvd.code if exc.rcvd else None
            reason = exc.rcvd.reason if exc.rcvd else ""
            log.warning("Gateway connection closed — code=%s reason=%s", code, reason)
            if code in (CLOSE_AUTH_FAILED, CLOSE_INVALID_PAYLOAD, CLOSE_REPLACED):
                break
            if not _should_resume(code):
                session.reset()
        except OSError as exc:
            session.connected = False
            log.warning("Gateway connect failed — %s", exc)
        except Exception as exc:
            session.connected = False
            log.exception("Unexpected gateway error — %s", exc)

        log.info("Reconnecting gateway in %.1fs …", RECONNECT_BACKOFF_SEC)
        await asyncio.sleep(RECONNECT_BACKOFF_SEC)

