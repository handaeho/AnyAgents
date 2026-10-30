import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import FastAPI, Header
import uvicorn

from agents import ollama_client
from api.agent import agent_service
from api.config import BOT_TOKEN, ENABLE_GATEWAY
from api.gateway import gateway_session, run_gateway_forever
from api.kakao_client import kakao_client
from api.schemas import (
    CallbackRequest,
    CommandsResponse,
    CommandsUpdateRequest,
    GuideResponse,
    GuideUpdateRequest,
    SendMessageRequest,
    SendMessageResponse,
    SkillResponse,
    WebhookMessageRequest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    gateway_task: asyncio.Task | None = None
    if ENABLE_GATEWAY:
        log.info("Starting Kakao Bot Gateway background task...")
        gateway_task = asyncio.create_task(run_gateway_forever(gateway_session))
    try:
        yield
    finally:
        if gateway_task and not gateway_task.done():
            gateway_task.cancel()
            try:
                await gateway_task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="AnyAgents Kakao Bot REST API",
    description="카카오톡 봇 REST API 및 AI 에이전트 연동 스켈레톤",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """서버 상태, 로컬 Ollama 모델 및 카카오 봇 게이트웨이 연결 상태를 확인합니다."""
    return {
        "status": "ok",
        "bot_token_configured": bool(BOT_TOKEN),
        "ollama": {
            "base_url": ollama_client.base_url,
            "model": ollama_client.model,
            "models_dir": str(ollama_client.models_dir),
            "manifest_found": ollama_client.is_model_installed(),
        },
        "gateway": {
            "enabled": ENABLE_GATEWAY,
            "connected": gateway_session.connected,
            "bot_id": gateway_session.bot_id,
            "session_id": gateway_session.session_id,
            "last_seq": gateway_session.last_seq,
        },
    }


# ── AI 에이전트 메시지 수신/응답 엔드포인트 ──────────────────────────

@app.post("/webhook", response_model=SkillResponse, tags=["Agent"])
@app.post("/agent/chat", response_model=SkillResponse, tags=["Agent"])
async def handle_user_message(request: WebhookMessageRequest) -> SkillResponse:
    """
    사용자 메시지를 수신하여 로컬 Ollama 모델(qwen3.8:27b) 기반 응답(SkillResponse)을 생성합니다.
    - callbackToken이 포함된 경우 카카오톡 콜백 API(/v1/bot/callback)로도 즉시 발송합니다.
    """
    skill_response = await agent_service.generate_reply(
        request.content,
        context=request.model_dump(exclude_none=True),
    )
    if request.callbackToken:
        await kakao_client.send_callback(request.callbackToken, skill_response)
    return skill_response


# ── 카카오톡 봇 REST API 엔드포인트 ───────────

@app.post("/v1/bot/callback", response_model=SendMessageResponse, tags=["메시지"])
async def bot_callback(
    request: CallbackRequest,
    x_bot_callback_token: Annotated[
        str,
        Header(alias="X-Bot-Callback-Token", description="카카오톡 서버에서 전달받은 봇 콜백 토큰 (5분 뒤 만료)"),
    ],
) -> SendMessageResponse:
    """특정 봇으로 콜백 응답 메시지를 발송합니다."""
    return await kakao_client.send_callback(x_bot_callback_token, request.skillResponse)


@app.post("/v1/bot/send_message", response_model=SendMessageResponse, tags=["메시지"])
async def bot_send_message(request: SendMessageRequest) -> SendMessageResponse:
    """봇이 있는 방에 먼저 메시지를 보냅니다 (botUserKey 또는 botGroupKey 필수)."""
    return await kakao_client.send_message(
        request.skillResponse,
        bot_user_key=request.botUserKey,
        bot_group_key=request.botGroupKey,
    )


@app.get("/v1/bot/commands", response_model=CommandsResponse, tags=["명령어"])
async def get_bot_commands() -> CommandsResponse:
    """앱과 연결된 봇에서 사용 중인 모든 명령어를 조회합니다."""
    return await kakao_client.get_commands()


@app.post("/v1/bot/commands/update", response_model=CommandsResponse, tags=["명령어"])
async def update_bot_commands(request: CommandsUpdateRequest) -> CommandsResponse:
    """앱과 연결된 봇에서 사용하고 있는 명령어를 새로 등록하거나 수정합니다."""
    return await kakao_client.update_commands(request.utterances)


@app.get("/v1/bot/guide", response_model=GuideResponse, tags=["도움말"])
async def get_bot_guide() -> GuideResponse:
    """앱과 연결된 봇의 도움말을 조회합니다."""
    return await kakao_client.get_guide()


@app.post("/v1/bot/guide/update", response_model=GuideResponse, tags=["도움말"])
async def update_bot_guide(request: GuideUpdateRequest) -> GuideResponse:
    """앱과 연결된 봇의 도움말을 수정합니다."""
    return await kakao_client.update_guide(request.contents)


def run() -> None:
    """uv run anyagents 실행 엔트리포인트"""
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()

