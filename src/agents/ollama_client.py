import logging
from pathlib import Path
import re
from typing import Any

import httpx

from api.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_MODELS,
    OLLAMA_THINK,
    OLLAMA_TIMEOUT,
)

log = logging.getLogger("agents.ollama")

_HYPHEN_TAG_RE = re.compile(r"^([a-zA-Z0-9._]+)-([0-9]+b(?:-[a-zA-Z0-9._]+)?)$")


def normalize_model_name(model: str) -> str:
    """'qwen3.8-27b' 형태 입력을 Ollama 표준 태그 'qwen3.8:27b'로 정규화합니다."""
    cleaned = model.strip()
    if ":" not in cleaned:
        match = _HYPHEN_TAG_RE.match(cleaned)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
    return cleaned


class OllamaClient:
    """로컬 Ollama 모델 연동 클라이언트"""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        models_dir: str = OLLAMA_MODELS,
        timeout: float = OLLAMA_TIMEOUT,
        think: bool = OLLAMA_THINK,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = normalize_model_name(model)
        self.models_dir = Path(models_dir).expanduser()
        self.timeout = timeout
        self.think = think

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

    async def chat(
        self,
        user_message: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """Ollama /api/chat 엔드포인트를 호출하여 응답 텍스트를 반환합니다."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": self.think,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = (data.get("message") or {}).get("content", "")
        return content.strip()


ollama_client = OllamaClient()

