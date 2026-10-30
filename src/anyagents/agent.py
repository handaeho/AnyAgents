import logging
from typing import Any
from anyagents.schemas import SkillResponse

log = logging.getLogger("anyagents.agent")


class AgentService:
    """AI 에이전트 응답 생성 서비스 (스켈레톤)"""

    GREETING_TRIGGER = "안녕하세요"
    GREETING_RESPONSE = "반갑습니다. 무엇이든 물어보세요."

    async def generate_reply(
        self,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> SkillResponse:
        """
        사용자 발화(user_message)를 받아 카카오 SkillResponse 객체를 생성합니다.
        추후 LLM / AI 에이전트 파이프라인을 이 메서드에 연결할 수 있습니다.
        """
        normalized = user_message.strip()
        log.info("Agent processing message: %r", normalized)

        if normalized == self.GREETING_TRIGGER or self.GREETING_TRIGGER in normalized:
            reply_text = self.GREETING_RESPONSE
        else:
            # 기본 에이전트 스켈레톤 응답 (향후 LLM 연동 지점)
            reply_text = f"전달받은 메시지: {normalized}"

        return SkillResponse.from_simple_text(reply_text)


agent_service = AgentService()

