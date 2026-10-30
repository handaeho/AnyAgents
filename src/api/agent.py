import logging
from typing import Any

from agents import ollama_client
from agents.memory import conversation_memory
from agents.prompts import bind_optional_request_context, handle_optional_command
from api.schemas import Component, SimpleText, SkillResponse, SkillTemplate

log = logging.getLogger("api.agent")

KAKAO_SIMPLE_TEXT_LIMIT = 1000
KAKAO_MAX_BUBBLES = 3


def split_into_kakao_bubbles(text: str) -> list[Component]:
    """긴 응답을 카카오톡 말풍선 제한(개당 1,000자, 최대 3개 = 3,000자)에 맞춰 분할합니다."""
    cleaned = text.strip()
    if not cleaned:
        return [Component(simpleText=SimpleText(text="응답을 생성하지 못했습니다."))]

    chunks: list[str] = []
    remaining = cleaned
    while remaining and len(chunks) < KAKAO_MAX_BUBBLES:
        if len(remaining) <= KAKAO_SIMPLE_TEXT_LIMIT:
            chunks.append(remaining)
            remaining = ""
            break

        if len(chunks) == KAKAO_MAX_BUBBLES - 1:
            chunks.append(remaining[: KAKAO_SIMPLE_TEXT_LIMIT - 1] + "…")
            remaining = ""
            break

        split_idx = remaining.rfind("\n", 0, KAKAO_SIMPLE_TEXT_LIMIT)
        if split_idx <= 0:
            split_idx = KAKAO_SIMPLE_TEXT_LIMIT
        chunks.append(remaining[:split_idx].strip())
        remaining = remaining[split_idx:].strip()

    return [Component(simpleText=SimpleText(text=chunk)) for chunk in chunks if chunk]


class AgentService:
    """로컬 Ollama 모델 기반 AI 에이전트 응답 생성 서비스"""

    async def generate_reply(
        self,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> SkillResponse:
        """
        사용자 발화(user_message)를 받아 로컬 Ollama 모델 응답으로 SkillResponse를 생성합니다.
        """
        normalized = user_message.strip()
        session_key = conversation_memory.resolve_session_key(context)
        log.info(
            "Agent processing message (session=%s, model=%s): %r",
            session_key,
            ollama_client.model,
            normalized,
        )

        if not normalized:
            return SkillResponse.from_simple_text("메시지를 입력해주세요.")

        if normalized in ("/초기화", "/reset"):
            conversation_memory.clear(session_key)
            return SkillResponse.from_simple_text("현재 대화 세션 메모리를 초기화했습니다.")

        history = conversation_memory.get_history(session_key)
        try:
            with bind_optional_request_context(context):
                routed_reply = await handle_optional_command(
                    normalized,
                    context=context,
                    history=history,
                )
                if routed_reply is not None:
                    reply_text = routed_reply
                else:
                    reply_text = await ollama_client.chat(normalized, history=history)
            if reply_text:
                conversation_memory.append_turn(session_key, normalized, reply_text)
        except Exception as exc:
            log.exception("Ollama 모델 호출 실패: %s", exc)
            reply_text = "모델 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

        if not reply_text:
            reply_text = "응답을 생성하지 못했습니다."

        return SkillResponse(
            version="2.0",
            template=SkillTemplate(outputs=split_into_kakao_bubbles(reply_text)),
        )


agent_service = AgentService()
