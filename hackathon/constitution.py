from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

log = logging.getLogger("hackathon.constitution")

KST = ZoneInfo("Asia/Seoul")
HACKATHON_DIR: Path = Path(__file__).resolve().parent
CONSTITUTION_PATH: Path = HACKATHON_DIR / "CONSTITUTION.md"
WORLD_STATE_PATH: Path = HACKATHON_DIR / "world_state.json"
HACKATHON_DATA_DIR: Path = HACKATHON_DIR / "data"


def load_constitution_text() -> str:
    """hackathon/CONSTITUTION.md 원문을 실시간으로 읽어 반환합니다."""
    try:
        if CONSTITUTION_PATH.is_file():
            return CONSTITUTION_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        log.warning("헌법 문서 로드 실패: %s", exc)
    return ""


def load_world_state() -> dict[str, Any]:
    """hackathon/world_state.json에서 현재 가상 도시 및 단서 상태를 로드합니다."""
    default_state: dict[str, Any] = {
        "city_name": "미정",
        "scenario_summary": "",
        "updated_at": "",
        "zones": {},
        "entities": {},
        "rules": [],
        "events": [],
        "facts": [],
        "hypotheses": [],
        "metrics": {},
    }
    try:
        if WORLD_STATE_PATH.is_file():
            raw = WORLD_STATE_PATH.read_text(encoding="utf-8")
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                default_state.update(loaded)
    except Exception as exc:
        log.warning("world_state.json 로드 실패: %s", exc)
    return default_state


def save_world_state(state: dict[str, Any]) -> dict[str, Any]:
    """hackathon/world_state.json에 갱신된 도시 상태를 저장합니다."""
    WORLD_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(KST).isoformat(timespec="seconds")
    WORLD_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return state


def build_hackathon_prompt_context() -> str:
    """통합 헌법, 실시간 도시 상태(world_state.json), 사전 검증 풀이 목록(solutions/)을 결합하여 반환합니다."""
    sections: list[str] = []
    constitution = load_constitution_text()
    if constitution:
        sections.append(constitution)

    world_state = load_world_state()
    state_json = json.dumps(world_state, ensure_ascii=False, indent=2)
    sections.append(
        "## 현재 누적된 가상 도시 상태 및 단서 (hackathon/world_state.json)\n"
        f"```json\n{state_json}\n```"
    )

    solutions_dir = HACKATHON_DIR / "solutions"
    if solutions_dir.is_dir():
        sol_files = sorted(
            str(p.relative_to(solutions_dir))
            for p in solutions_dir.rglob("*")
            if p.is_file() and p.name != "README.md"
        )
        if sol_files:
            sol_list_str = "\n".join(f"- {f}" for f in sol_files)
            sections.append(
                "## Codex/Gemini가 검증 완료한 사전 풀이 목록 (hackathon/solutions/)\n"
                "질문이 아래 목록과 관련 있다면 반드시 `search_solutions` 도구(action='read')로 먼저 읽으세요.\n"
                f"{sol_list_str}"
            )
    return "\n\n".join(sections)
