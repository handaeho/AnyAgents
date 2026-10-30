from pathlib import Path
import re

from agents.tools import register_tool
from hackathon.constitution import HACKATHON_DIR

SOLUTIONS_DIR: Path = HACKATHON_DIR / "solutions"
MAX_READ_CHARS = 8000


def _resolve_safe_solution_path(relative_path: str) -> Path:
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    base = SOLUTIONS_DIR.resolve()
    target = (base / relative_path).resolve()
    if base not in target.parents and target != base:
        raise ValueError("hackathon/solutions 외부 경로는 접근할 수 없습니다.")
    return target


def list_solution_files() -> list[str]:
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        str(p.relative_to(SOLUTIONS_DIR))
        for p in SOLUTIONS_DIR.rglob("*")
        if p.is_file() and p.name != "README.md"
    )


@register_tool(
    name="search_solutions",
    description=(
        "Codex/Gemini가 사전 검증하여 hackathon/solutions/에 저장해 둔 문제 풀이 및 정답 문서를 조회하거나 검색합니다. "
        "질문에 답하기 전에 이미 검증된 해답이 있는지 먼저 확인하세요."
    ),
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "'list' (풀이 파일 목록), 'read' (특정 풀이 읽기), 'search' (키워드 검색) 중 선택",
            },
            "file_path": {
                "type": "string",
                "description": "hackathon/solutions/ 기준 상대 경로 (read 시 필수)",
            },
            "query": {
                "type": "string",
                "description": "search 액션일 때 검색할 키워드 또는 정규식",
            },
        },
        "required": ["action"],
    },
)
def search_solutions(
    action: str = "list",
    file_path: str = "",
    query: str = "",
) -> str:
    SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)

    if action == "list":
        files = list_solution_files()
        if not files:
            return "현재 hackathon/solutions/에 저장된 사전 풀이 문서가 없습니다."
        return "저장된 검증 풀이 목록:\n" + "\n".join(f"- {f}" for f in files)

    if action == "read":
        if not file_path:
            return "read 액션에는 file_path가 필요합니다."
        target = _resolve_safe_solution_path(file_path)
        if not target.is_file():
            return f"풀이 파일을 찾을 수 없습니다: {file_path}"
        content = target.read_text(encoding="utf-8", errors="replace")
        if len(content) > MAX_READ_CHARS:
            return content[:MAX_READ_CHARS] + f"\n...(총 {len(content)}자 중 앞 {MAX_READ_CHARS}자 표시)"
        return content

    if action == "search":
        if not query:
            return "search 액션에는 query가 필요합니다."
        regex = re.compile(query, re.IGNORECASE)
        matches: list[str] = []
        for rel_str in list_solution_files():
            path = _resolve_safe_solution_path(rel_str)
            for line_no, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(),
                start=1,
            ):
                if regex.search(line):
                    matches.append(f"{rel_str}:{line_no}: {line.strip()}")
                    if len(matches) >= 50:
                        break
        if not matches:
            return f"'{query}'와 일치하는 사전 풀이 내용이 없습니다."
        return "\n".join(matches)

    return f"지원하지 않는 action입니다: {action} ('list', 'read', 'search' 중 선택)"

