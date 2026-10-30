import asyncio
import sys

from agents.tools import register_tool
from hackathon.constitution import HACKATHON_DIR

PYTHON_EXEC_TIMEOUT_SEC = 15.0
MAX_OUTPUT_CHARS = 4000


@register_tool(
    name="run_python",
    description=(
        "수리 최적화, 경로 탐색, 일정/예산 계산, 데이터/로그 집계 및 가설 검증을 위해 Python 코드를 실행하고 표준 출력을 반환합니다. "
        "암산하지 말고 반드시 이 도구로 계산 결과를 print()하여 검증하세요."
    ),
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "실행할 Python 스크립트 코드 (결과는 반드시 print()로 출력, 작업 디렉터리는 hackathon/)",
            },
        },
        "required": ["code"],
    },
)
async def run_python(code: str = "") -> str:
    cleaned = code.strip()
    if not cleaned:
        return "실행할 Python 코드가 비어 있습니다."

    HACKATHON_DIR.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        cleaned,
        cwd=str(HACKATHON_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=PYTHON_EXEC_TIMEOUT_SEC,
        )
    except TimeoutError:
        proc.kill()
        await proc.communicate()
        return f"Python 실행 시간 초과 ({PYTHON_EXEC_TIMEOUT_SEC}초 제한)"

    stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
    stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()

    output_parts: list[str] = [f"[exit_code={proc.returncode}]"]
    if stdout_text:
        output_parts.append(f"STDOUT:\n{stdout_text}")
    if stderr_text:
        output_parts.append(f"STDERR:\n{stderr_text}")
    if not stdout_text and not stderr_text:
        output_parts.append("(출력 없음 — 결과를 확인하려면 print()를 사용하세요)")

    combined = "\n".join(output_parts)
    if len(combined) > MAX_OUTPUT_CHARS:
        return combined[:MAX_OUTPUT_CHARS] + "\n...(출력 길이 제한으로 생략됨)"
    return combined

