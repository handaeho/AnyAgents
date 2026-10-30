import logging
from typing import Any

from agents import ollama_client
from api.schemas import SkillResponse

log = logging.getLogger("api.agent")

KAKAO_SIMPLE_TEXT_LIMIT = 1000


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
        log.info("Agent processing message (model=%s): %r", ollama_client.model, normalized)

        if not normalized:
            return SkillResponse.from_simple_text("메시지를 입력해주세요.")

        try:
            reply_text = await ollama_client.chat(normalized)
        except Exception as exc:
            log.exception("Ollama 모델 호출 실패: %s", exc)
            reply_text = "모델 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

        if not reply_text:
            reply_text = "응답을 생성하지 못했습니다."

        if len(reply_text) > KAKAO_SIMPLE_TEXT_LIMIT:
            reply_text = reply_text[: KAKAO_SIMPLE_TEXT_LIMIT - 1] + "…"

        return SkillResponse.from_simple_text(reply_text)


agent_service = AgentService()
