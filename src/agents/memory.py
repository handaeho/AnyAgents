from collections import defaultdict
from typing import Any

MAX_HISTORY_MESSAGES = 20


class ConversationMemory:
    """세션 키(botGroupKey 또는 botUserKey) 기반 인메모리 멀티턴 대화 저장소"""

    def __init__(self, max_messages: int = MAX_HISTORY_MESSAGES) -> None:
        self.max_messages = max_messages
        self._store: dict[str, list[dict[str, str]]] = defaultdict(list)

    @staticmethod
    def resolve_session_key(context: dict[str, Any] | None) -> str:
        if not context:
            return "default"
        return (
            str(
                context.get("botGroupKey")
                or context.get("botUserKey")
                or context.get("channelId")
                or context.get("userId")
                or "default"
            )
            .strip()
            or "default"
        )

    def get_history(self, session_key: str) -> list[dict[str, str]]:
        return list(self._store.get(session_key, ()))

    def append_turn(self, session_key: str, user_message: str, assistant_reply: str) -> None:
        history = self._store[session_key]
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_reply})
        if len(history) > self.max_messages:
            self._store[session_key] = history[-self.max_messages :]

    def clear(self, session_key: str) -> None:
        self._store.pop(session_key, None)

    def clear_all(self) -> None:
        self._store.clear()


conversation_memory = ConversationMemory()

