import html
import logging
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

log = logging.getLogger("agents.web_search")

DDG_HTML_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_RESULT_LINK_RE = re.compile(
    r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.DOTALL,
)
_RESULT_SNIPPET_RE = re.compile(
    r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")

WEB_SEARCH_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "최신 뉴스, 실시간 정보, 인물/사건/기술 사실 확인이 필요할 때 무료 웹 검색(DuckDuckGo)을 수행합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 키워드 또는 질문",
                },
            },
            "required": ["query"],
        },
    },
}


def _clean_html(raw: str) -> str:
    return html.unescape(_TAG_RE.sub("", raw)).strip()


def _extract_ddg_url(href: str) -> str:
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    if "uddg" in qs and qs["uddg"]:
        return unquote(qs["uddg"][0])
    return href


async def search_web(query: str, max_results: int = 5) -> str:
    """DuckDuckGo HTML 엔드포인트를 통해 무료 웹 검색 결과를 텍스트로 반환합니다."""
    cleaned_query = query.strip()
    if not cleaned_query:
        return "검색어가 비어 있습니다."

    log.info("Executing web_search: query=%r", cleaned_query)
    headers = {"User-Agent": USER_AGENT}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.post(DDG_HTML_URL, data={"q": cleaned_query}, headers=headers)
            resp.raise_for_status()
            body = resp.text
    except Exception as exc:
        log.warning("Web search request failed: %s", exc)
        return f"웹 검색 호출 실패: {exc}"

    links = _RESULT_LINK_RE.findall(body)
    snippets = _RESULT_SNIPPET_RE.findall(body)

    results: list[str] = []
    for idx, (href, raw_title) in enumerate(links[:max_results], start=1):
        title = _clean_html(raw_title)
        url = _extract_ddg_url(html.unescape(href))
        snippet = _clean_html(snippets[idx - 1]) if idx - 1 < len(snippets) else ""
        results.append(f"[{idx}] {title}\nURL: {url}\n요약: {snippet}")

    if not results:
        return f"'{cleaned_query}'에 대한 웹 검색 결과가 없습니다."

    return "\n\n".join(results)

