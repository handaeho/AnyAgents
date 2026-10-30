import logging
from pathlib import Path
import re
from typing import Any

import httpx

from agents.prompts import build_runtime_system_prompt
from agents.tools import execute_registered_tool, get_tool_schemas
from api.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_MODELS,
    OLLAMA_THINK,
    OLLAMA_TIMEOUT,
    OLLAMA_WEB_SEARCH,
)

log = logging.getLogger("agents.ollama")

_HYPHEN_TAG_RE = re.compile(r"^([a-zA-Z0-9._]+)-([0-9]+b(?:-[a-zA-Z0-9._]+)?)$")
MAX_TOOL_ROUNDS = 5


def _build_system_prompt(custom_prompt: str | None = None) -> str:
    return build_runtime_system_prompt(custom_prompt)


def normalize_model_name(model: str) -> str:
    """'qwen3.8-27b' 형태 입력을 Ollama 표준 태그 'qwen3.8:27b'로 정규화합니다."""
    cleaned = model.strip()
    if ":" not in cleaned:
        match = _HYPHEN_TAG_RE.match(cleaned)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
    return cleaned


class OllamaClient:
    """로컬 Ollama 모델 연동 클라이언트 (Thinking 및 무료 웹 검색 Tool Calling 지원)"""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        models_dir: str = OLLAMA_MODELS,
        timeout: float = OLLAMA_TIMEOUT,
        think: bool = OLLAMA_THINK,
        web_search_enabled: bool = OLLAMA_WEB_SEARCH,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = normalize_model_name(model)
        self.models_dir = Path(models_dir).expanduser()
        self.timeout = timeout
        self.think = think
        self.web_search_enabled = web_search_enabled

    def manifest_path(self) -> Path:
        """로컬 Ollama 모델 매니페스트 파일 경로를 반환합니다."""
        name, _, tag = self.model.partition(":")
        tag = tag or "latest"
        return self.models_dir / "manifests" / "registry.ollama.ai" / "library" / name / tag

    def is_model_installed(self) -> bool:
        """지정된 OLLAMA_MODELS 경로에 모델 매니페스트가 존재하는지 확인합니다."""
        try:
            return self.manifest_path().is_file()
        except OSError:
            return False

    async def _execute_tool(self, name: str, arguments: dict[str, Any] | str) -> str:
        return await execute_registered_tool(name, arguments)

    async def chat(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Ollama /api/chat 엔드포인트를 호출하며, 필요 시 Tool Calling 루프를 수행합니다."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _build_system_prompt(system_prompt)},
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tools = get_tool_schemas(include_web_search=self.web_search_enabled)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for round_idx in range(MAX_TOOL_ROUNDS + 1):
                payload: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "think": self.think,
                }
                if tools and round_idx < MAX_TOOL_ROUNDS:
                    payload["tools"] = tools

                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()

                message = data.get("message") or {}
                tool_calls = message.get("tool_calls") or []

                if not tool_calls or round_idx >= MAX_TOOL_ROUNDS:
                    content = message.get("content", "")
                    return content.strip()

                messages.append(message)
                for call in tool_calls:
                    fn = call.get("function") or {}
                    fn_name = fn.get("name", "")
                    fn_args = fn.get("arguments") or {}
                    log.info(
                        "Tool call requested (round=%d): name=%s args=%s",
                        round_idx + 1,
                        fn_name,
                        fn_args,
                    )
                    tool_output = await self._execute_tool(fn_name, fn_args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": fn_name,
                            "content": tool_output,
                        }
                    )

        return ""


ollama_client = OllamaClient()
