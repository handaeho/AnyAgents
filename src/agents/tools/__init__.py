from collections.abc import Awaitable, Callable
import inspect
import json
import logging
from typing import Any

from agents.prompts import _load_hackathon_module

log = logging.getLogger("agents.tools")

ToolHandler = Callable[..., Awaitable[str] | str]

_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {}
_TOOL_HANDLERS: dict[str, ToolHandler] = {}


def register_tool(
    *,
    name: str,
    description: str,
    parameters: dict[str, Any],
) -> Callable[[ToolHandler], ToolHandler]:
    """Ollama Tool Calling 규격으로 도구를 레지스트리에 등록하는 데코레이터"""

    def decorator(func: ToolHandler) -> ToolHandler:
        _TOOL_SCHEMAS[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        _TOOL_HANDLERS[name] = func
        return func

    return decorator


def get_tool_schemas(include_web_search: bool = True) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for name, schema in _TOOL_SCHEMAS.items():
        if name == "web_search" and not include_web_search:
            continue
        schemas.append(schema)
    return schemas


def parse_tool_arguments(arguments: dict[str, Any] | str | None) -> dict[str, Any]:
    if not arguments:
        return {}
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            loaded = json.loads(arguments)
            return loaded if isinstance(loaded, dict) else {"value": loaded}
        except json.JSONDecodeError:
            return {"query": arguments}
    return {}


async def execute_registered_tool(name: str, arguments: dict[str, Any] | str | None) -> str:
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        return f"지원하지 않는 도구입니다: {name}"

    parsed_args = parse_tool_arguments(arguments)
    try:
        result = handler(**parsed_args)
        if inspect.isawaitable(result):
            return str(await result)
        return str(result)
    except TypeError:
        try:
            result = handler(parsed_args)
            if inspect.isawaitable(result):
                return str(await result)
            return str(result)
        except Exception as exc:
            log.exception("Tool execution failed (%s): %s", name, exc)
            return f"도구 실행 오류 ({name}): {exc}"
    except Exception as exc:
        log.exception("Tool execution failed (%s): %s", name, exc)
        return f"도구 실행 오류 ({name}): {exc}"


# 1. 일반(Core) 내장 도구 로드
from agents.tools import web_search_tool as _web_search_tool  # noqa: E402, F401

# 2. 해커톤 디렉터리(hackathon/)가 존재할 때만 해커톤 전용 도구 자동 마운트
_hackathon_mod = _load_hackathon_module()
if _hackathon_mod is not None:
    _hackathon_mod.register_hackathon_tools()
