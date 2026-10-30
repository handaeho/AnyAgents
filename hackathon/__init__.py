from contextlib import contextmanager
import json
import logging
from typing import Any

from hackathon.bridge import (
    current_request_context,
    enqueue_and_wait_heavy_task,
    read_latest_outbox,
    read_status,
)
from hackathon.constitution import build_hackathon_prompt_context, load_world_state
from hackathon.router import route_user_message

log = logging.getLogger("hackathon")


def register_hackathon_tools() -> None:
    """해커톤 전용 도구들을 범용 도구 레지스트리에 등록합니다."""
    from hackathon.tools import custom_tools as _custom_tools  # noqa: F401
    from hackathon.tools import heavy_agent_bridge as _heavy_agent_bridge  # noqa: F401
    from hackathon.tools import python_runner as _python_runner  # noqa: F401
    from hackathon.tools import solution_bank as _solution_bank  # noqa: F401
    from hackathon.tools import workspace_io as _workspace_io  # noqa: F401
    from hackathon.tools import world_state as _world_state  # noqa: F401


@contextmanager
def bind_request_context(context: dict[str, Any] | None):
    token = current_request_context.set(context)
    try:
        yield
    finally:
        current_request_context.reset(token)


async def handle_hackathon_message(
    user_message: str,
    *,
    context: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> str | None:
    """
    해커톤 모드 메시지 통합 엔트리포인트:
    1. 관리자용 슬래시 명령어(/상태, /결과, /위임)가 들어오면 즉시 처리합니다.
    2. 일반 자연어 질문(심사위원/사용자)이 들어오면 내부 자동 라우터(router.py)가 난이도를 판별합니다:
       - SOLUTION_HIT: 사전 검증된 풀이(hackathon/solutions/)를 즉시 활용해 답변
       - COMPLEX: 슬래시 명령 없이도 자동으로 inbox.md에 등록 후 Codex/Gemini 정답(outbox.md) 반환 (시간 초과 시 로컬 qwen3.8 자동 폴백)
       - SIMPLE: None을 반환하여 기본 로컬 qwen3.8 파이프라인으로 즉시 실행
    """
    command = user_message.strip()

    # 1. 운영자 디버그용 명령어 (유지하되 심사위원은 사용할 필요 없음)
    if command in ("/상태", "/state"):
        state_dump = json.dumps(load_world_state(), ensure_ascii=False, indent=2)
        return f"[현재 도시 상태]\n{state_dump}"

    if command in ("/결과", "/outbox"):
        status = read_status()
        header = f"[위임 상태: {status.get('status', 'idle')} | ID: {status.get('task_id')}]\n"
        return header + read_latest_outbox()

    for prefix in ("/위임 ", "/codex ", "/gemini "):
        if command.startswith(prefix):
            question = command[len(prefix) :].strip()
            if not question:
                return f"사용법: `{prefix.strip()} <해결할 고난도 질문>`"
            return await enqueue_and_wait_heavy_task(
                question=question,
                reason=f"수동 위임 ({prefix.strip()})",
                context=context,
                history=history,
            )

    # 2. 심사위원/사용자 자연어 질문 자동 라우팅
    decision, payload_or_reason = await route_user_message(command)

    if decision == "SOLUTION_HIT" and payload_or_reason:
        from agents import ollama_client

        sol_prompt = (
            "아래는 상위 에이전트(Codex/Gemini)가 이미 파이썬으로 검증을 마친 공식 해답 데이터입니다. "
            "별도의 재계산 없이 아래 검증된 해답을 바탕으로 사용자의 질문에 자연스럽고 명확하게 답변하세요.\n\n"
            f"{payload_or_reason}"
        )
        return await ollama_client.chat(command, system_prompt=sol_prompt, history=history)

    if decision == "COMPLEX":
        return await enqueue_and_wait_heavy_task(
            question=command,
            reason=payload_or_reason or "내부 자동 라우터가 고난도 문제로 판별",
            context=context,
            history=history,
            allow_local_fallback=True,
        )

    # SIMPLE 인 경우 None 반환 -> 기본 로컬 qwen3.8 실행
    return None


__all__ = [
    "bind_request_context",
    "build_hackathon_prompt_context",
    "handle_hackathon_message",
    "register_hackathon_tools",
]
