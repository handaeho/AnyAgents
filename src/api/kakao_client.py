import logging
from typing import Any
import httpx
from fastapi import HTTPException

from api.config import BOT_TOKEN, KAKAO_API_URL
from api.schemas import (
    CallbackRequest,
    CommandsResponse,
    CommandsUpdateRequest,
    GuideResponse,
    GuideUpdateRequest,
    SendMessageRequest,
    SendMessageResponse,
    SkillResponse,
    UtteranceRequest,
)

log = logging.getLogger("api.kakao_client")


class KakaoBotClient:
    """카카오톡 봇 REST API 클라이언트 """

    def __init__(self, bot_token: str = BOT_TOKEN, base_url: str = KAKAO_API_URL) -> None:
        self.bot_token = bot_token
        self.base_url = base_url.rstrip("/")

    def _auth_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        if not self.bot_token:
            raise HTTPException(
                status_code=500,
                detail="BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.",
            )
        headers = {
            "Authorization": f"KakaoAK {self.bot_token}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        req_headers = self._auth_headers(headers)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(method, url, headers=req_headers, json=json_body)

        if resp.status_code >= 400:
            log.error("Kakao API error [%s %s]: %d %s", method, path, resp.status_code, resp.text)
            try:
                err_detail = resp.json()
            except Exception:
                err_detail = resp.text
            raise HTTPException(status_code=resp.status_code, detail=err_detail)

        return resp.json()

    async def send_callback(
        self,
        callback_token: str,
        skill_response: SkillResponse,
    ) -> SendMessageResponse:
        """
        메시지 콜백 API
        POST https://kapi.kakao.com/v1/bot/callback
        """
        payload = CallbackRequest(skillResponse=skill_response).model_dump(exclude_none=True)
        data = await self._request(
            "POST",
            "/v1/bot/callback",
            headers={"X-Bot-Callback-Token": callback_token},
            json_body=payload,
        )
        return SendMessageResponse.model_validate(data)

    async def send_message(
        self,
        skill_response: SkillResponse,
        *,
        bot_user_key: str | None = None,
        bot_group_key: str | None = None,
    ) -> SendMessageResponse:
        """
        메시지 전송 API
        POST https://kapi.kakao.com/v1/bot/send_message
        """
        payload = SendMessageRequest(
            botUserKey=bot_user_key,
            botGroupKey=bot_group_key,
            skillResponse=skill_response,
        ).model_dump(exclude_none=True)
        data = await self._request("POST", "/v1/bot/send_message", json_body=payload)
        return SendMessageResponse.model_validate(data)

    async def get_commands(self) -> CommandsResponse:
        """
        명령어 전체 조회 API
        GET https://kapi.kakao.com/v1/bot/commands
        """
        data = await self._request("GET", "/v1/bot/commands")
        return CommandsResponse.model_validate(data)

    async def update_commands(self, utterances: list[UtteranceRequest]) -> CommandsResponse:
        """
        명령어 전체 수정 API
        POST https://kapi.kakao.com/v1/bot/commands/update
        """
        payload = CommandsUpdateRequest(utterances=utterances).model_dump()
        data = await self._request("POST", "/v1/bot/commands/update", json_body=payload)
        return CommandsResponse.model_validate(data)

    async def get_guide(self) -> GuideResponse:
        """
        도움말 조회 API
        GET https://kapi.kakao.com/v1/bot/guide
        """
        data = await self._request("GET", "/v1/bot/guide")
        return GuideResponse.model_validate(data)

    async def update_guide(self, contents: str) -> GuideResponse:
        """
        도움말 수정 API
        POST https://kapi.kakao.com/v1/bot/guide/update
        """
        payload = GuideUpdateRequest(contents=contents).model_dump()
        data = await self._request("POST", "/v1/bot/guide/update", json_body=payload)
        return GuideResponse.model_validate(data)


kakao_client = KakaoBotClient()

