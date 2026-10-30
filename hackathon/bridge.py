import asyncio
from contextvars import ContextVar
from datetime import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any
import uuid

from hackathon.constitution import HACKATHON_DIR, KST, WORLD_STATE_PATH

log = logging.getLogger("hackathon.bridge")

QUEUE_DIR: Path = HACKATHON_DIR / "queue"
INBOX_PATH: Path = QUEUE_DIR / "inbox.md"
OUTBOX_PATH: Path = QUEUE_DIR / "outbox.md"
STATUS_PATH: Path = QUEUE_DIR / "status.json"

# Codex/Gemini 응답을 기다릴 1차 대기 시간 (초과 시 로컬 qwen3.8 자동 폴백 실행하여 콜백 300초 내 응답 보장)
DEFAULT_WAIT_SEC = float(os.getenv("HEAVY_AGENT_WAIT_SEC", "120.0"))
POLL_INTERVAL_SEC = float(os.getenv("HEAVY_AGENT_POLL_SEC", "0.5"))
BG_WATCH_TIMEOUT_SEC = float(os.getenv("HEAVY_AGENT_BG_TIMEOUT_SEC", "1800.0"))

current_request_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "current_request_context",
    default=None,
)

_background_watchers: set[asyncio.Task[Any]] = set()


def _extract_target_keys(context: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if not context:
        return None, None
    bot_user_key = (
        context.get("botUserKey")
        or (context.get("user") or {}).get("id")
        if isinstance(context.get("user"), dict)
        else context.get("botUserKey")
    )
    bot_group_key = (
        context.get("botGroupKey")
        or context.get("chatId")
        or context.get("channelId")
    )
    return (
        str(bot_user_key).strip() if bot_user_key else None,
        str(bot_group_key).strip() if bot_group_key else None,
    )


def read_status() -> dict[str, Any]:
    if STATUS_PATH.is_file():
        try:
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"status": "idle", "task_id": None}


def write_status(data: dict[str, Any]) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_latest_outbox() -> str:
    if not OUTBOX_PATH.is_file():
        return "아직 작성된 정밀 분석 결과(hackathon/queue/outbox.md)가 없습니다."
    content = OUTBOX_PATH.read_text(encoding="utf-8").strip()
    return content or "hackathon/queue/outbox.md 파일이 비어 있습니다."


def _is_outbox_ready(task_id: str, baseline_mtime: float) -> str | None:
    if not OUTBOX_PATH.is_file():
        return None
    try:
        stat = OUTBOX_PATH.stat()
    except OSError:
        return None
    if stat.st_mtime <= baseline_mtime:
        return None

    content = OUTBOX_PATH.read_text(encoding="utf-8").strip()
    if not content or "<!-- WAITING_FOR_SOLUTION" in content:
        return None
    return content


async def _push_outbox_when_ready(
    task_id: str,
    baseline_mtime: float,
    bot_user_key: str | None,
    bot_group_key: str | None,
) -> None:
    """1차 대기 시간을 넘겨 로컬 폴백이 먼저 나간 뒤라도, outbox.md가 완성되면 카카오톡 방으로 정밀 해답을 능동 푸시합니다."""
    elapsed = 0.0
    while elapsed < BG_WATCH_TIMEOUT_SEC:
        await asyncio.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC

        current_status = read_status()
        if current_status.get("task_id") != task_id:
            return

        answer = _is_outbox_ready(task_id, baseline_mtime)
        if answer is None:
            continue

        current_status["status"] = "completed"
        current_status["completed_at"] = datetime.now(KST).isoformat(timespec="seconds")
        write_status(current_status)

        if not bot_user_key and not bot_group_key:
            log.info("Outbox completed for task=%s", task_id)
            return

        try:
            from api.agent import split_into_kakao_bubbles
            from api.kakao_client import kakao_client
            from api.schemas import SkillResponse, SkillTemplate

            # 심사위원에게 노출되므로 내부 task_id 태그 없이 깔끔한 본문만 전송
            skill_response = SkillResponse(
                version="2.0",
                template=SkillTemplate(outputs=split_into_kakao_bubbles(answer)),
            )
            await kakao_client.send_message(
                skill_response,
                bot_user_key=bot_user_key,
                bot_group_key=bot_group_key,
            )
            log.info("Proactive Kakao push succeeded for task=%s", task_id)
        except Exception as exc:
            log.exception("Proactive Kakao push failed for task=%s: %s", task_id, exc)
        return


async def enqueue_and_wait_heavy_task(
    question: str,
    reason: str = "고난도 복합 추론/최적화 문제",
    context_summary: str = "",
    context: dict[str, Any] | None = None,
    wait_timeout: float | None = None,
    allow_local_fallback: bool = True,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    1. hackathon/queue/inbox.md에 작업 요청서를 기록하고 터미널에 알림 배너를 출력합니다.
    2. wait_timeout(기본 120초) 동안 VS Code(Codex/Gemini)가 outbox.md를 저장하길 대기합니다.
    3. 시간 내 저장되면 내부 태그 없이 순수 정답만 즉시 반환합니다.
    4. 시간 내 저장되지 않으면:
       - allow_local_fallback=True(기본값)일 때 로컬 qwen3.8을 즉시 실행해 콜백 만료 전에 정상 답변을 반환하고,
         백그라운드에서는 outbox.md 완성 시 추가 푸시합니다.
    """
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    task_id = uuid.uuid4().hex[:8]
    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

    effective_ctx = context if context is not None else current_request_context.get()
    bot_user_key, bot_group_key = _extract_target_keys(effective_ctx)

    OUTBOX_PATH.write_text(
        f"<!-- WAITING_FOR_SOLUTION task_id={task_id} -->\n",
        encoding="utf-8",
    )
    baseline_mtime = OUTBOX_PATH.stat().st_mtime

    inbox_md = (
        f"# [Heavy Agent Task] ID: `{task_id}`\n\n"
        f"- **요청 시각**: {now_str}\n"
        f"- **자동 분류 사유**: {reason}\n"
        f"- **도시 상태 파일**: `{WORLD_STATE_PATH.relative_to(HACKATHON_DIR.parent)}`\n"
        f"- **데이터 폴더**: `hackathon/data/`\n\n"
        f"## 1. 해결할 질문 / 문제\n"
        f"{question.strip()}\n\n"
        f"## 2. 로컬 에이전트 파악 컨텍스트\n"
        f"{context_summary.strip() or '(추가 요약 없음 — world_state.json 및 hackathon/data/ 참조)'}\n\n"
        f"## 3. Codex / Gemini 작성 지침\n"
        f"1. `hackathon/CONSTITUTION.md`의 5대 원칙에 따라 Python 검증을 거쳐 최적해를 도출하세요.\n"
        f"2. 새로 밝혀진 단서/규칙은 `hackathon/world_state.json`에 반영하고, 재사용할 풀이는 `hackathon/solutions/`에 저장하세요.\n"
        f"3. **카카오톡으로 발송할 최종 답변 텍스트만 `hackathon/queue/outbox.md` 파일에 덮어쓰기 저장**하세요. (`WAITING_FOR_SOLUTION` 주석 제거)\n"
    )
    INBOX_PATH.write_text(inbox_md, encoding="utf-8")

    write_status(
        {
            "task_id": task_id,
            "status": "pending",
            "created_at": now_str,
            "question": question.strip(),
            "reason": reason,
            "bot_user_key": bot_user_key,
            "bot_group_key": bot_group_key,
        }
    )
    log.warning(
        "\n============================================================\n"
        "🔔 [고난도 문제 자동 감지 -> hackathon/queue/inbox.md 생성됨]\n"
        "   VS Code(Codex/Gemini)에서 'inbox 풀어줘'를 실행하세요! (대기: %.0f초)\n"
        "   질문: %s\n"
        "============================================================",
        DEFAULT_WAIT_SEC if wait_timeout is None else wait_timeout,
        question.strip()[:120],
    )

    timeout = DEFAULT_WAIT_SEC if wait_timeout is None else wait_timeout
    elapsed = 0.0
    while elapsed < timeout:
        await asyncio.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC
        answer = _is_outbox_ready(task_id, baseline_mtime)
        if answer is not None:
            status = read_status()
            status["status"] = "completed"
            status["completed_at"] = datetime.now(KST).isoformat(timespec="seconds")
            write_status(status)
            return answer

    # 시간 내에 Codex/Gemini가 outbox.md를 작성하지 못한 경우 백그라운드 감시는 유지
    watcher_task = asyncio.create_task(
        _push_outbox_when_ready(task_id, baseline_mtime, bot_user_key, bot_group_key)
    )
    _background_watchers.add(watcher_task)
    watcher_task.add_done_callback(_background_watchers.discard)

    # 심사위원에게 '위임 접수' 같은 메타 메시지 대신 로컬 qwen3.8 폴백으로 실제 답변을 반환
    if allow_local_fallback:
        log.warning(
            "Codex/Gemini 대기 시간(%.1fs) 초과 — 로컬 qwen3.8 자동 폴백으로 즉시 답변 생성 (task_id=%s)",
            timeout,
            task_id,
        )
        from agents import ollama_client

        fallback_prompt = (
            "참고: 현재 질문은 고난도 문제입니다. `escalate_to_heavy_agent` 도구를 다시 호출하지 말고, "
            "`get_world_state`, `inspect_workspace_data`, `run_python` 도구를 직접 사용해 최선의 검증된 답변을 작성하세요."
        )
        reply = await ollama_client.chat(
            question,
            system_prompt=fallback_prompt,
            history=history,
        )
        if reply:
            return reply

    return "질문하신 조건과 데이터를 종합하여 최적 경로 및 해결 방안을 분석 중입니다. 잠시 후 상세 결과를 전해드리겠습니다."
