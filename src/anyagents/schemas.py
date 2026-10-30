from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


# ── 공통 객체 (Common Objects) ───────────────────────────────────────

class Link(BaseModel):
    mobile: str | None = None
    pc: str | None = None
    web: str | None = None


class Thumbnail(BaseModel):
    imageUrl: str
    link: Link | None = None
    fixedRatio: bool | None = None
    altText: str | None = Field(default=None, max_length=50)


class Profile(BaseModel):
    nickname: str
    imageUrl: str


ButtonAction = Literal[
    "message",
    "webLink",
    "phone",
    "share",
    "operator",
    "invite",
    "mention",
    "inviteMember",
    "settings",
    "guide",
]


class Button(BaseModel):
    action: ButtonAction
    label: str = Field(..., max_length=14)
    messageText: str | None = None
    webLinkUrl: str | None = None
    phoneNumber: str | None = None
    extra: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_required_fields_by_action(self) -> Button:
        if self.action == "message" and not self.messageText:
            raise ValueError("action이 'message'인 경우 messageText는 필수입니다.")
        if self.action == "webLink" and not self.webLinkUrl:
            raise ValueError("action이 'webLink'인 경우 webLinkUrl은 필수입니다.")
        if self.action == "phone" and not self.phoneNumber:
            raise ValueError("action이 'phone'인 경우 phoneNumber는 필수입니다.")
        return self


ButtonLayout = Literal["vertical", "horizontal"]


# ── 말풍선 컴포넌트 (Bubble Components) ──────────────────────────────

class SimpleText(BaseModel):
    text: str = Field(..., max_length=1000)


class SimpleImage(BaseModel):
    imageUrl: str
    altText: str | None = Field(default=None, max_length=50)


class TextCard(BaseModel):
    title: str = Field(..., max_length=50)
    description: str = Field(..., max_length=400)
    buttons: list[Button] = Field(..., max_length=3)
    buttonLayout: ButtonLayout | None = None


class BasicCard(BaseModel):
    title: str = Field(..., max_length=50)
    description: str = Field(..., max_length=230)
    thumbnail: Thumbnail
    buttons: list[Button] = Field(..., max_length=3)
    buttonLayout: ButtonLayout | None = None


class ListItem(BaseModel):
    title: str
    imageUrl: str | None = None
    link: Link | None = None
    description: str | None = None
    messageText: str | None = None
    extra: dict[str, Any] | None = None
    action: Literal["message"] | None = None


class ListCard(BaseModel):
    header: ListItem
    items: list[ListItem] = Field(..., max_length=5)
    buttons: list[Button] = Field(..., max_length=3)
    buttonLayout: ButtonLayout | None = None


class ImageTitle(BaseModel):
    title: str
    description: str | None = None
    imageUrl: str | None = None


class Head(BaseModel):
    title: str


class Item(BaseModel):
    title: str = Field(..., max_length=6)
    description: str


class ItemListSummary(BaseModel):
    title: str = Field(..., max_length=6)
    description: str = Field(..., max_length=14)


class ItemCard(BaseModel):
    itemList: list[Item] = Field(..., max_length=10)
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=200)
    head: Head | None = None
    imageTitle: ImageTitle | None = None
    itemListAlignment: Literal["left", "right"] | None = None
    itemListSummary: ItemListSummary | None = None
    thumbnail: Thumbnail | None = None
    profile: Profile | None = None
    buttons: list[Button] = Field(..., max_length=3)
    buttonLayout: ButtonLayout | None = None


class CommerceCard(BaseModel):
    price: int
    currency: Literal["won"] = "won"
    thumbnails: list[Thumbnail] = Field(..., min_length=1, max_length=1)
    buttons: list[Button] = Field(..., max_length=3)
    title: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, max_length=40)
    discount: int | None = None
    discountRate: int | None = None
    discountedPrice: int | None = None
    profile: Profile | None = None
    buttonLayout: ButtonLayout | None = None


class CarouselHeader(BaseModel):
    title: str
    description: str
    thumbnail: Thumbnail


CarouselCardType = Literal["basicCard", "commerceCard", "listCard", "itemCard", "textCard"]
CardUnion = BasicCard | CommerceCard | ListCard | ItemCard | TextCard


class Carousel(BaseModel):
    type: CarouselCardType
    items: list[CardUnion] = Field(..., max_length=10)
    header: CarouselHeader | None = None


class Component(BaseModel):
    simpleText: SimpleText | None = None
    simpleImage: SimpleImage | None = None
    textCard: TextCard | None = None
    basicCard: BasicCard | None = None
    commerceCard: CommerceCard | None = None
    listCard: ListCard | None = None
    itemCard: ItemCard | None = None
    carousel: Carousel | None = None


# ── 스킬 응답 객체 (SkillResponse & SkillTemplate) ───────────────────

class QuickReply(BaseModel):
    label: str
    action: Literal["message"] = "message"
    messageText: str | None = None
    extra: dict[str, Any] | None = None


class SkillTemplate(BaseModel):
    outputs: list[Component] = Field(..., min_length=1, max_length=3)
    quickReplies: list[QuickReply] | None = Field(default=None, max_length=10)


class SkillResponse(BaseModel):
    version: Literal["2.0"] = "2.0"
    template: SkillTemplate
    extra: dict[str, Any] | None = None

    @classmethod
    def from_simple_text(
        cls,
        text: str,
        quick_replies: list[QuickReply] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> SkillResponse:
        return cls(
            version="2.0",
            template=SkillTemplate(
                outputs=[Component(simpleText=SimpleText(text=text))],
                quickReplies=quick_replies,
            ),
            extra=extra,
        )


# ── REST API 요청/응답 스키마 ────────────────────────────────────────

class CallbackRequest(BaseModel):
    skillResponse: SkillResponse


class SendMessageRequest(BaseModel):
    botUserKey: str | None = None
    botGroupKey: str | None = None
    skillResponse: SkillResponse

    @model_validator(mode="after")
    def check_target_key(self) -> SendMessageRequest:
        if not self.botUserKey and not self.botGroupKey:
            raise ValueError("botUserKey 또는 botGroupKey 중 하나는 필수입니다.")
        return self


class SendMessageResponse(BaseModel):
    totalCount: int
    sendCount: int
    errorCount: int


class UtteranceRequest(BaseModel):
    buttonName: str
    description: str | None = None


class CommandsUpdateRequest(BaseModel):
    utterances: list[UtteranceRequest] = Field(..., max_length=30)


class UtteranceResponse(BaseModel):
    id: str
    type: Literal["TEXT"] = "TEXT"
    value: str
    buttonName: str
    description: str | None = None


class CommandsResponse(BaseModel):
    utterances: list[UtteranceResponse]


class GuideUpdateRequest(BaseModel):
    contents: str


class GuideResponse(BaseModel):
    contents: str
    createdAt: str
    updatedAt: str | None = None


class WebhookMessageRequest(BaseModel):
    """웹훅 또는 테스트용 사용자 메시지 입력 스키마"""
    content: str = Field(..., description="사용자가 보낸 메시지 텍스트")
    callbackToken: str | None = Field(
        default=None,
        description="콜백 토큰 (전달 시 카카오 콜백 API로도 즉시 발송)",
    )
    botUserKey: str | None = None
    botGroupKey: str | None = None

