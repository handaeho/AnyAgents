from contextlib import contextmanager
from datetime import datetime
import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent.parent

log = logging.getLogger("agents.prompts")

KST = ZoneInfo("Asia/Seoul")
_WEEKDAY_KO = ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")

DEFAULT_ANYARCHIVE_PROMPT = (
    "당신은 AnyArchive 솔루션의 공식 AI 고객지원 챗봇입니다. "
    "사용자의 문의에 정확하고 친절하며 간결하게 답변하세요."
)


def is_hackathon_enabled() -> bool:
    """루트 hackathon/ 디렉터리가 존재하고 ENABLE_HACKATHON 환경변수가 활성화된 경우에만 True를 반환합니다."""
    env_flag = os.getenv("ENABLE_HACKATHON", "true").lower() in ("1", "true", "yes")
    return env_flag and (BASE_DIR / "hackathon" / "__init__.py").is_file()


def _load_hackathon_module():
    if not is_hackathon_enabled():
        return None
    base_str = str(BASE_DIR)
    if base_str not in sys.path:
        sys.path.insert(0, base_str)
    try:
        return importlib.import_module("hackathon")
    except Exception as exc:
        log.warning("해커톤 모듈 로드 실패 (일반 모드로 폴백): %s", exc)
        return None


def build_runtime_system_prompt(custom_prompt: str | None = None) -> str:
    """현재 KST 시각과 활성 모드(해커톤 헌법 또는 AnyArchive 기본 프롬프트)를 결합합니다."""
    now = datetime.now(KST)
    weekday = _WEEKDAY_KO[now.weekday()]
    date_context = (
        f"현재 시각은 대한민국 표준시(KST) 기준 {now.strftime('%Y년 %m월 %d일')} {weekday} "
        f"{now.strftime('%H:%M')}입니다. '오늘', '현재', '최신', '올해' 등의 시간 표현은 "
        f"별도 기준 시각이 명시되지 않은 한 {now.strftime('%Y년 %m월 %d일')}을 기준으로 판단하세요."
    )

    sections: list[str] = [date_context]

    hackathon_mod = _load_hackathon_module()
    if hackathon_mod is not None:
        sections.append(hackathon_mod.build_hackathon_prompt_context())
    else:
        sections.append(DEFAULT_ANYARCHIVE_PROMPT)

    if custom_prompt:
        sections.append(custom_prompt)

    return "\n\n".join(sections)


async def handle_optional_command(
    command: str,
    context: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> str | None:
    """해커톤 모드가 활성화된 경우 내부 자동 라우팅 및 전용 명령어를 위임 처리합니다."""
    hackathon_mod = _load_hackathon_module()
    if hackathon_mod is not None and hasattr(hackathon_mod, "handle_hackathon_message"):
        res = hackathon_mod.handle_hackathon_message(
            command,
            context=context,
            history=history,
        )
        if inspect.isawaitable(res):
            return await res
        return res
    return None


@contextmanager
def bind_optional_request_context(context: dict[str, Any] | None):
    """요청 컨텍스트(botUserKey/botGroupKey 등)를 하위 도구에 안전하게 전달합니다."""
    hackathon_mod = _load_hackathon_module()
    if hackathon_mod is not None and hasattr(hackathon_mod, "bind_request_context"):
        with hackathon_mod.bind_request_context(context):
            yield
    else:
        yield
