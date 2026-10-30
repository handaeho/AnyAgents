from pathlib import Path
import re

from agents.tools import register_tool
from hackathon.constitution import HACKATHON_DATA_DIR

MAX_READ_CHARS = 8000


def _resolve_safe_path(relative_path: str) -> Path:
    HACKATHON_DATA_DIR.mkdir(parents=True, exist_ok=True)
    base = HACKATHON_DATA_DIR.resolve()
    target = (base / relative_path).resolve()
    if base not in target.parents and target != base:
        raise ValueError("hackathon/data 외부 경로는 접근할 수 없습니다.")
    return target


@register_tool(
    name="inspect_workspace_data",
    description=(
        "hackathon/data/ 폴더 내의 문제 데이터 파일 목록을 조회하거나, 특정 파일의 내용을 읽고 키워드/정규식을 검색합니다."
    ),
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "'list' (파일 목록 조회), 'read' (파일 내용 읽기), 'search' (키워드/정규식 검색) 중 선택",
            },
            "file_path": {
                "type": "string",
                "description": "hackathon/data/ 기준 상대 파일 경로 (read 또는 특정 파일 search 시 사용)",
            },
            "pattern": {
                "type": "string",
                "description": "search 액션일 때 검색할 키워드 또는 정규표현식",
            },
        },
        "required": ["action"],
    },
)
def inspect_workspace_data(
    action: str = "list",
    file_path: str = "",
    pattern: str = "",
) -> str:
    HACKATHON_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if action == "list":
        files = sorted(
            str(p.relative_to(HACKATHON_DATA_DIR))
            for p in HACKATHON_DATA_DIR.rglob("*")
            if p.is_file()
        )
        if not files:
            return "hackathon/data/ 내에 파일이 없습니다."
        return "hackathon/data/ 파일 목록:\n" + "\n".join(f"- {f}" for f in files)

    if action == "read":
        if not file_path:
            return "read 액션에는 file_path가 필요합니다."
        target = _resolve_safe_path(file_path)
        if not target.is_file():
            return f"파일을 찾을 수 없습니다: {file_path}"
        content = target.read_text(encoding="utf-8", errors="replace")
        if len(content) > MAX_READ_CHARS:
            return content[:MAX_READ_CHARS] + f"\n...(총 {len(content)}자 중 앞 {MAX_READ_CHARS}자 표시)"
        return content

    if action == "search":
        if not pattern:
            return "search 액션에는 pattern이 필요합니다."
        regex = re.compile(pattern, re.IGNORECASE)
        targets = (
            [_resolve_safe_path(file_path)]
            if file_path
            else sorted(p for p in HACKATHON_DATA_DIR.rglob("*") if p.is_file())
        )
        matches: list[str] = []
        for path in targets:
            if not path.is_file():
                continue
            rel = path.relative_to(HACKATHON_DATA_DIR)
            for line_no, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(),
                start=1,
            ):
                if regex.search(line):
                    matches.append(f"{rel}:{line_no}: {line.strip()}")
                    if len(matches) >= 50:
                        break
            if len(matches) >= 50:
                break
        if not matches:
            return f"패턴 '{pattern}'과 일치하는 결과가 없습니다."
        return "\n".join(matches)

    return f"지원하지 않는 action입니다: {action} ('list', 'read', 'search' 중 선택)"

