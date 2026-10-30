from agents.tools import register_tool
from hackathon.bridge import enqueue_and_wait_heavy_task


@register_tool(
    name="escalate_to_heavy_agent",
    description=(
        "다중 제약 수리 최적화, 복잡한 모호한 단서 교차 추론, 대규모 파일 정밀 분석 등 로컬 모델(qwen3.8)만으로 확신하기 어려운 "
        "고난도 문제를 VS Code의 상위 에이전트(Codex / Gemini)에게 위임합니다. "
        "hackathon/queue/inbox.md에 문제를 기록하고 hackathon/queue/outbox.md의 최종 해답을 받아 반환합니다."
    ),
    parameters={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "상위 에이전트(Codex/Gemini)가 해결해야 할 전체 질문 및 요구사항",
            },
            "reason": {
                "type": "string",
                "description": "위임하는 이유 (예: 다중 구역 경로 최적화 및 복합 제약 검증 필요)",
            },
            "context_summary": {
                "type": "string",
                "description": "현재까지 파악된 관련 단서나 파일 경로 요약",
            },
        },
        "required": ["question", "reason"],
    },
)
async def escalate_to_heavy_agent(
    question: str = "",
    reason: str = "고난도 복합 추론 문제",
    context_summary: str = "",
) -> str:
    return await enqueue_and_wait_heavy_task(
        question=question,
        reason=reason,
        context_summary=context_summary,
    )

