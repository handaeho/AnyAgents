from agents.tools import register_tool
from agents.web_search import search_web


@register_tool(
    name="web_search",
    description="최신 뉴스, 실시간 정보, 인물/사건/기술 사실 확인이 필요할 때 무료 웹 검색(DuckDuckGo)을 수행합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색할 키워드 또는 질문",
            },
        },
        "required": ["query"],
    },
)
async def web_search_handler(query: str = "") -> str:
    return await search_web(query)

