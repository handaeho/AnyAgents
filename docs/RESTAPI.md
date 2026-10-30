# 카카오톡 봇 REST API

이 문서는 REST API를 사용한 봇 API 구현 방법을 안내합니다.

---

## 메시지

### 메시지 콜백

#### 기본 정보

| 메서드 | URL | 인증 방식 |
| :--- | :--- | :--- |
| POST | `https://kapi.kakao.com/v1/bot/callback` | 봇 인증 토큰 |

| 요구 사항 | 참고 |
| :--- | :--- |
| 봇 생성 | 에러 코드<br>FAQ |

특정 봇으로 응답 메시지를 발송합니다.

##### 봇 콜백 토큰

콜백 메시지 발송 권한을 검증을 위한 봇 콜백 토큰을 헤더에 함께 전달해야 합니다. 콜백 토큰은 카카오톡 서버로부터 전달 받은 후 5분 뒤에 만료됩니다.

#### 요청

##### 헤더

| 이름 | 설명 | 필수 |
| :--- | :--- | :--- |
| `Authorization` | 봇 생성 시 발급되는 봇 인증 토큰으로 인증 요청<br>`Authorization: KakaoAK ${BOT_TOKEN}` | O |
| `X-Bot-Callback-Token` | 봇 콜백 토큰, 메시지 발송 권한 검증에 사용하는 커스텀 헤더<br>카카오톡 서버에서 전달받은 후 5분 뒤 만료 | O |

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `skillResponse` | `SkillResponse` | 발송할 카카오 봇 스킬 객체, 카카오 i 오픈빌더 스킬 응답 포맷 사용, 메시지 전송 API 요청 본문과 동일 | O |

#### 응답

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `totalCount` | `Integer` | 전체 발송 대상 말풍선 수 | O |
| `sendCount` | `Integer` | 발송 성공 수 | O |
| `errorCount` | `Integer` | 발송 실패 수 | O |

#### 예제

##### 요청

- SimpleText
- SimpleImage
- TextCard
- BasicCard
- CommerceCard
- ListCard
- ItemCard
- Carousel

```bash
curl -X POST "https://kapi.kakao.com/v1/bot/callback" \
  -H "Authorization: KakaoAK ${BOT_TOKEN}" \
  -H "X-Bot-Callback-Token: ${BOT_CALLBACK_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "skillResponse": {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "simpleText": {
              "text": "처리가 완료되었습니다."
            }
          }
        ]
      }
    }
  }'
```

##### 응답: 성공

```json
// HTTP/1.1 200 OK
// Content-Type: application/json;charset=UTF-8
{
  "totalCount": 1,
  "sendCount": 1,
  "errorCount": 0
}
```

---

### 메시지 전송

#### 기본 정보

| 메서드 | URL | 인증 방식 |
| :--- | :--- | :--- |
| POST | `https://kapi.kakao.com/v1/bot/send_message` | 봇 인증 토큰 |

| 요구 사항 | 참고 |
| :--- | :--- |
| 봇 생성 | 에러 코드<br>FAQ |

봇이 있는 방에 먼저 메시지를 보낼 수 있습니다.

단, 채널채팅은 채널 친구여야 하며 일반채팅, 오픈채팅은 방에 초대되어야 합니다.

#### 요청

##### 헤더

| 이름 | 설명 | 필수 |
| :--- | :--- | :--- |
| `Authorization` | 봇 생성 시 발급되는 봇 인증 토큰으로 인증 요청<br>`Authorization: KakaoAK ${BOT_TOKEN}` | O |

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `botUserKey` | `String` | 채널채팅 발송 시 사용 | X* |
| `botGroupKey` | `String` | 일반채팅, 오픈채팅, 팀채팅 발송 시 사용 | X* |
| `skillResponse` | `SkillResponse` | 발송할 카카오 봇 스킬 응답 객체 | O |

\* `botUserKey` 또는 `botGroupKey` 중 하나 필수

##### SkillResponse

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `version` | `String` | 스킬 응답 버전<br>현재 `"2.0"`만 지원 | O |
| `template` | `SkillTemplate` | 말풍선과 퀵리플라이에 사용할 템플릿 | O |
| `extra` | `JSON` | 부가 정보(키는 String, 값은 Object 형식)<br>사용자 멘션 시 멘션할 사용자 정보 입력 | X |

##### SkillTemplate

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `outputs` | `Component[]` | 말풍선 컴포넌트 목록(최소: 1개, 최대: 3개) | O |
| `quickReplies` | `QuickReply[]` | 빠른 답장 목록(최대: 10개) | X |

##### Component

| 이름 | 타입 | 설명 |
| :--- | :--- | :--- |
| `simpleText` | `SimpleText` | 심플 텍스트 |
| `simpleImage` | `SimpleImage` | 심플 이미지 |
| `textCard` | `TextCard` | 텍스트 카드 |
| `basicCard` | `BasicCard` | 베이식 카드 |
| `commerceCard` | `CommerceCard` | 커머스 카드 |
| `listCard` | `ListCard` | 리스트 카드 |
| `itemCard` | `ItemCard` | 아이템 카드 |
| `carousel` | `Carousel` | 캐러셀 |

##### QuickReply

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `label` | `String` | 사용자에게 노출되는 바로가기 응답 표시 | O |
| `action` | `Enum` | 바로가기 응답 기능<br>- `message`: 선택한 발화가 그대로 전달 | O |
| `messageText` | `String` | 사용자에게 노출되는 발화 | X |
| `extra` | `JSON` | 블록 호출 시 스킬 서버에 추가 전달하는 정보(키는 String, 값은 Object 형식) | X |

#### 응답

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `totalCount` | `Integer` | 전체 발송 대상 말풍선 수 | O |
| `sendCount` | `Integer` | 발송 성공 수 | O |
| `errorCount` | `Integer` | 발송 실패 수 | O |

#### 예제

##### 요청

- SimpleText
- SimpleImage
- TextCard
- BasicCard
- CommerceCard
- ListCard
- ItemCard
- Carousel

```bash
curl -X POST "https://kapi.kakao.com/v1/bot/send_message" \
  -H "Authorization: KakaoAK ${BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "botGroupKey": "grp456",
    "skillResponse": {
      "version": "2.0",
      "template": {
        "outputs": [
          {
            "simpleText": {
              "text": "안녕하세요!"
            }
          }
        ]
      }
    }
  }'
```

##### 응답: 성공

```json
// HTTP/1.1 200 OK
// Content-Type: application/json;charset=UTF-8
{
  "totalCount": 1,
  "sendCount": 1,
  "errorCount": 0
}
```

---

## 명령어

### 명령어 전체 조회

#### 기본 정보

| 메서드 | URL | 인증 방식 |
| :--- | :--- | :--- |
| GET | `https://kapi.kakao.com/v1/bot/commands` | 봇 인증 토큰 |

| 요구 사항 | 참고 |
| :--- | :--- |
| 봇 생성 | 에러 코드<br>FAQ |

앱과 연결된 봇에서 사용 중인 모든 명령어를 반환합니다.

#### 요청

##### 헤더

| 이름 | 설명 | 필수 |
| :--- | :--- | :--- |
| `Authorization` | 봇 생성 시 발급되는 봇 인증 토큰으로 인증 요청<br>`Authorization: KakaoAK ${BOT_TOKEN}` | O |

#### 응답

응답은 명령어 목록을 포함한 JSON 객체입니다. 요청 실패 시 에러 코드로 원인을 확인합니다.

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `utterances` | `UtteranceResponse[]` | 명령어 목록 | O |

##### UtteranceResponse

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `id` | `String` | 명령어 ID | O |
| `type` | `Enum` | 명령어 타입<br>- `TEXT`: 텍스트 발화 | O |
| `value` | `String` | 명령어 이름 | O |
| `buttonName` | `String` | 버튼 이름 | O |
| `description` | `String` | 명령어 내용, 미설정 시 `null` | X |

#### 예제

##### 요청

```bash
curl -X GET "https://kapi.kakao.com/v1/bot/commands" \
  -H "Authorization: KakaoAK ${BOT_TOKEN}"
```

##### 응답: 성공

```json
// HTTP/1.1 200 OK
// Content-Type: application/json;charset=UTF-8
{
  "utterances": [
    {
      "id": "66a1b2c3d4e5f6a7b8c9d0e1",
      "type": "TEXT",
      "value": "도움말",
      "buttonName": "도움말",
      "description": null
    }
  ]
}
```

---

### 명령어 전체 수정

#### 기본 정보

| 메서드 | URL | 인증 방식 |
| :--- | :--- | :--- |
| POST | `https://kapi.kakao.com/v1/bot/commands/update` | 봇 인증 토큰 |

| 요구 사항 | 참고 |
| :--- | :--- |
| 봇 생성 | 에러 코드<br>FAQ |

앱과 연결된 봇에서 사용하고 있는 명령어를 새로 등록하거나 수정합니다.

#### 요청

##### 헤더

| 이름 | 설명 | 필수 |
| :--- | :--- | :--- |
| `Authorization` | 봇 생성 시 발급되는 봇 인증 토큰으로 인증 요청<br>`Authorization: KakaoAK ${BOT_TOKEN}` | O |

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `utterances` | `UtteranceRequest[]` | 명령어 목록(최대: 30개) | O |

##### UtteranceRequest

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `buttonName` | `String` | 버튼 이름 | O |
| `description` | `String` | 명령어 설명, 미설정 시 `null` | X |

#### 응답

##### 본문

요청 성공 시 응답은 명령어 전체 조회 응답 본문과 동일합니다. 요청 실패 시 에러 코드로 원인을 확인합니다.

#### 예제

##### 요청

```bash
curl -X POST "https://kapi.kakao.com/v1/bot/commands/update" \
  -H "Authorization: KakaoAK ${BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "utterances": [
      {
        "buttonName": "도움말",
        "description": null
      },
      {
        "buttonName": "상담원 연결",
        "description": "상담원과 연결합니다."
      }
    ]
  }'
```

##### 응답: 성공

```json
// HTTP/1.1 200 OK
// Content-Type: application/json;charset=UTF-8
{
  "utterances": [
    {
      "id": "66a1b2c3d4e5f6a7b8c9d0e1",
      "type": "TEXT",
      "value": "도움말",
      "buttonName": "도움말",
      "description": null
    },
    {
      "id": "66a1b2c3d4e5f6a7b8c9d0e2",
      "type": "TEXT",
      "value": "상담 연결",
      "buttonName": "상담원 연결",
      "description": "상담원과 연결합니다."
    }
  ]
}
```

##### 응답: 실패

```json
// HTTP/1.1 400 Bad Request
// Content-Type: application/json;charset=UTF-8
{
  "code": -870,
  "msg": "TalkBotCommonException",
  "extras": {
    "code": 10001,
    "message": "유효하지 않은 앱입니다."
  }
}
```

---

## 도움말

### 도움말 조회

#### 기본 정보

| 메서드 | URL | 인증 방식 |
| :--- | :--- | :--- |
| GET | `https://kapi.kakao.com/v1/bot/guide` | 봇 인증 토큰 |

| 요구 사항 | 참고 |
| :--- | :--- |
| 봇 생성 | 에러 코드<br>FAQ |

앱과 연결된 봇의 도움말을 반환합니다.

#### 요청

##### 헤더

| 이름 | 설명 | 필수 |
| :--- | :--- | :--- |
| `Authorization` | 봇 생성 시 발급되는 봇 인증 토큰으로 인증 요청<br>`Authorization: KakaoAK ${BOT_TOKEN}` | O |

#### 응답

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `contents` | `String` | 도움말 내용 | O |
| `createdAt` | `Datetime` | 도움말 생성 일시 | O |
| `updatedAt` | `Datetime` | 도움말 수정 일시, 수정 사항이 없다면 `null` | X |

#### 예제

##### 요청

```bash
curl -X GET "https://kapi.kakao.com/v1/bot/guide" \
  -H "Authorization: KakaoAK ${BOT_TOKEN}"
```

##### 응답: 성공

```json
// HTTP/1.1 200 OK
// Content-Type: application/json;charset=UTF-8
{
  "contents": "🤖 저와 함께 이런 것들을 할 수 있어요.",
  "createdAt": "2024-03-01T09:00:00+09:00",
  "updatedAt": null
}
```

---

### 도움말 수정

#### 기본 정보

| 메서드 | URL | 인증 방식 |
| :--- | :--- | :--- |
| POST | `https://kapi.kakao.com/v1/bot/guide/update` | 봇 인증 토큰 |

| 요구 사항 | 참고 |
| :--- | :--- |
| 봇 생성 | 에러 코드<br>FAQ |

앱과 연결된 봇의 도움말을 수정합니다.

#### 요청

##### 헤더

| 이름 | 설명 | 필수 |
| :--- | :--- | :--- |
| `Authorization` | 봇 생성 시 발급되는 봇 인증 토큰으로 인증 요청<br>`Authorization: KakaoAK ${BOT_TOKEN}` | O |

##### 본문

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `contents` | `String` | 수정할 도움말 내용 | O |

#### 응답

##### 본문

요청 성공 시 응답은 도움말 조회 응답 본문과 동일합니다. 요청 실패 시 에러 코드로 원인을 확인합니다.

#### 예제

##### 요청

```bash
curl -X POST  "https://kapi.kakao.com/v1/bot/guide/update" \
  -H "Authorization: KakaoAK ${BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": "안녕하세요! 저는 카카오 챗봇입니다."
  }'
```

##### 응답: 성공

```json
// HTTP/1.1 200 OK
// Content-Type: application/json;charset=UTF-8
{
  "contents": "안녕하세요! 저는 카카오 챗봇입니다.",
  "createdAt": "2024-03-01T09:00:00+09:00",
  "updatedAt": "2024-03-10T15:30:00+09:00"
}
```

---

## 말풍선 컴포넌트

봇 API에서 사용하는 말풍선 컴포넌트의 필드 명세입니다. 말풍선 종류와 용도는 이해하기 > 말풍선을 참고합니다.

`SkillResponse`의 `outputs`에 아래 컴포넌트를 넣어 응답합니다. 최소 1개, 최대 3개까지 전달할 수 있습니다. 말풍선별 요청 본문 예제는 메시지 콜백 API 요청 예제 또는 메시지 전송 API 요청 예제 탭을 참고합니다.

### SimpleText

텍스트만 포함하는 말풍선입니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `text` | `String` | 전달 텍스트(최대: 1,000자)<br>- 500자 초과 시 이후 글자는 생략되고 전체 보기 버튼으로 전체 내용 확인 가능<br>- 사용자 멘션 시 멘션할 위치에 `{{#mentions.{userKey}}}` 형식으로 입력 | O |

#### 사용자 멘션

챗봇이 응답 시 사용자를 멘션할 수 있습니다. 단, 채널채팅은 지원하지 않습니다.

`text`에서 멘션을 넣을 위치에 `{{#mentions.{userKey}}}` 형식으로 입력하고, `SkillResponse`의 `extra.mentions.{userKey}`에 멘션할 사용자 정보를 입력합니다. `userKey`는 임의의 값으로 지정할 수 있으며, `extra.mentions.{userKey}`의 `type`과 `id`를 참조해 실제 멘션으로 대체됩니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `extra.mentions.{userKey}` | `JSON` | `text`에서 지정한 사용자 멘션 키 | O |
| `extra.mentions.{userKey}.type` | `String` | 사용자 식별 ID 타입, `botUserKey`로 고정 | O |
| `extra.mentions.{userKey}.id` | `String` | 사용자 ID 값 | O |

##### 제약 사항

- 멘션은 `SimpleText`에서만 동작합니다.
- 멘션은 한 응답에 최대 15명까지 가능합니다.

아래는 사용자 멘션을 포함한 `SkillResponse` 예제입니다.

```json
{
  "version": "2.0",
  "template": {
    "outputs": [
      {
        "simpleText": {
          "text": "🚀 주간 리더보드\n * 1위: {{#mentions.user1}}: 210점\n * 2위: {{#mentions.user2}}: 110점\n * 3위: {{#mentions.user3}}: 70점"
        }
      }
    ]
  },
  "extra": {
    "mentions": {
      "user1": {
        "type": "botUserKey",
        "id": "123abc456def789ghi"
      },
      "user2": {
        "type": "botUserKey",
        "id": "234b5c6d7e8f9g0h1i2j3k4l"
      },
      "user3": {
        "type": "botUserKey",
        "id": "345c6d7e8f9g0h1i2j3k4l5m"
      }
    }
  }
}
```

---

### SimpleImage

이미지만 포함하는 말풍선입니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `imageUrl` | `String` | 이미지 URL, 전달한 이미지 URL를 스크랩해 사용자에게 전달 | O |
| `altText` | `String` | 스크린 리더 대체 텍스트<br>최대 글자수: 50자 | X |

---

### TextCard

텍스트 카드형 말풍선입니다. 채널채팅에서 캐러셀 형태 사용 시, 텍스트 카드로 구성할 수 있습니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 카드 제목<br>- 최대 글자 수: 50자<br>- 글자 색상: 검정색 | O |
| `description` | `String` | 카드 상세 설명<br>- 최대<br>  - 단일형: `title`의 글자수를 포함해 400자<br>  - 캐러셀형: 128자<br>- 글자 색상: 검정색(`title`과 함께 사용 시 `description`은 회색으로 노출) | O |
| `buttons` | `Button[]` | 카드 버튼<br>- 최대<br>  - 가로 정렬: 2개<br>  - 세로 정렬: 3개 | O |
| `buttonLayout` | `Enum` | 버튼 정렬<br>- `vertical`: 세로<br>- `horizontal`: 가로 | X |

---

### BasicCard

베이식 카드형 말풍선입니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 카드 제목<br>- 최대 글자 수: 50자<br>- 글자 색상: 검정색 | O |
| `description` | `String` | 카드 상세 설명<br>- 최대 글자 수: 230자<br>- 글자 색상: 검정색(`title`과 함께 사용 시 `description`은 회색으로 노출) | O |
| `thumbnail` | `Thumbnail` | 카드 상단 이미지 | O |
| `buttons` | `Button[]` | 카드 버튼<br>- 최대<br>  - 가로 정렬: 2개<br>  - 세로 정렬: 3개 | O |
| `buttonLayout` | `Enum` | 버튼 정렬<br>- `vertical`: 세로<br>- `horizontal`: 가로 | X |

---

### ListCard

리스트 카드형 말풍선입니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `header` | `ListItem` | 카드 상단 항목 | O |
| `items` | `ListItem[]` | 카드 아이템<br>- 최대<br>  - 단일형: 5개<br>  - 캐러셀형: 4개 | O |
| `buttons` | `Button[]` | 카드 버튼<br>- 최대<br>  - 가로 정렬: 2개<br>  - 세로 정렬: 3개 | O |
| `buttonLayout` | `Enum` | 버튼 정렬<br>- `vertical`: 세로<br>- `horizontal`: 가로 | X |

#### ListItem

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | `header`에 사용 시 카드 제목, `items`에 사용 시 항목 제목 | O |
| `imageUrl` | `String` | `items`에 사용 시 항목 우측 안내 사진 | X |
| `link` | `Link` | 선택 시 이동할 플랫폼별 링크 정보<br>- PC 환경 우선순위: `pc` → `web`<br>- 모바일 환경 우선순위: `mobile` → `web` | X |
| `description` | `String` | `items`에 사용 시 항목 설명<br>`header`에는 미적용 | X |
| `messageText` | `String` | `action`이 `message`일 때 사용자 발화로 전송할 텍스트 | X |
| `extra` | `JSON` | 블록 호출 시 스킬 서버에 추가 전달하는 정보(키는 String, 값은 Object 형식) | X |
| `action` | `Enum` | 선택 시 수행 작업<br>- `message` | X |

---

### ItemCard

아이템 카드형 말풍선입니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `itemList` | `Item[]` | 아이템 목록<br>- 최대<br>  - 단일형: 10개<br>  - 캐러셀형: 5개 | O |
| `title` | `String` | 아이템 제목<br>- 최대<br>  - 단일형: 200자, 12줄<br>  - 캐러셀형: 100자, 12줄 | O |
| `description` | `String` | 설명<br>- 최대<br>  - 단일형: 200자, 12줄<br>  - 캐러셀형: 100자, 12줄 | O |
| `head` | `Head` | 헤드 정보<br>- `profile`과 동시 노출 불가<br>- 캐러셀 구성 시, 일부 카드에만 적용할 수 없으며 일괄 적용 필수 | O |
| `imageTitle` | `ImageTitle` | 이미지를 동반하는 제목 및 설명<br>- 이미지는 우측 정렬로 고정<br>- 캐러셀 구성 시, 일부 카드에만 적용할 수 없으며 일괄 적용 필수 | X |
| `itemListAlignment` | `Enum` | `itemList` 정렬<br>- `left`<br>- `right` | X |
| `itemListSummary` | `ItemListSummary` | 아이템 가격 정보 | X |
| `thumbnail` | `Thumbnail` | 상단 이미지<br>- 단일형: 2:1(800x400 픽셀) 또는 1:1(800x800 픽셀)<br>- 캐러셀형: 2:1만 가능<br>- 캐러셀 구성 시, 일부 카드에만 적용할 수 없으며 일괄 적용 필수 | X |
| `profile` | `Profile` | 프로필 정보<br>- `head`와 동시 노출 불가<br>- 캐러셀 구성 시, 일부 카드에만 적용할 수 없으며 일괄 적용 필수 | X |
| `buttons` | `Button[]` | 카드 버튼<br>- 최대<br>  - 가로 정렬: 2개<br>  - 세로 정렬: 3개<br>- `Button`에서 `share` 액션 사용 시 일부 필드만 공유됨 | O |
| `buttonLayout` | `Enum` | 버튼 정렬<br>- `vertical`: 세로<br>- `horizontal`: 가로 | X |

#### ImageTitle

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 제목 | O |
| `description` | `String` | 설명 | X |
| `imageUrl` | `String` | 이미지 URL | X |

#### Head

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 헤드 제목 | O |

#### Item

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 아이템 항목 제목(최대: 6자) | O |
| `description` | `String` | 아이템 항목 설명(최대: 2줄) | O |

#### ItemListSummary

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 요약 제목(최대: 6자) | O |
| `description` | `String` | 요약 설명(최대: 14자)<br>통화기호, 숫자, 콤마, 소수점, 공백만 허용 | O |

---

### CommerceCard

커머스 카드형 말풍선입니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `price` | `Integer` | 제품 가격 | O |
| `currency` | `String` | 가격 통화<br>`won`으로 고정 | O |
| `thumbnails` | `Thumbnail[]` | 제품 사진<br>현재 1개만 가능 | O |
| `buttons` | `Button[]` | 카드 버튼<br>- 최대<br>  - 가로 정렬: 2개<br>  - 세로 정렬: 3개 | O |
| `title` | `String` | 제품 이름(최대: 30자) | X |
| `description` | `String` | 제품 상세 설명(최대: 40자) | X |
| `discount` | `Integer` | 할인 금액 | X |
| `discountRate` | `Integer` | 할인율 | X |
| `discountedPrice` | `Integer` | 할인가 | X |
| `profile` | `Profile` | 제품 판매 프로필 정보 | X |
| `buttonLayout` | `Enum` | 버튼 정렬<br>- `vertical`: 세로<br>- `horizontal`: 가로 | X |

---

### Carousel

캐러셀형 말풍선입니다. 채널채팅만 지원합니다.

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `type` | `Enum` | 캐러셀 카드 타입<br>- `basicCard`<br>- `commerceCard`<br>- `listCard`<br>- `itemCard`<br>- `textCard` | O |
| `items` | `Card[]` | 캐러셀 아이템(최대: 10개, `listCard`는 5개) | O |
| `header` | `CarouselHeader` | 캐러셀 커버<br>`textCard`, `listCard` 캐러셀은 미지원 | O |

#### CarouselHeader

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `title` | `String` | 캐러셀 헤드 제목(최대: 2줄) | O |
| `description` | `String` | 캐러셀 헤드 설명(최대: 3줄) | O |
| `thumbnail` | `Thumbnail` | 캐러셀 헤드 배경 이미지<br>현재 `imageUrl`만 지원, 캐러셀 내 모든 이미지는 정사각형(1:1) 또는 와이드형(2:1)으로 통일 필요 | O |

---

## 공통 객체

### Button

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `action` | `Enum` | 버튼 선택 시 수행 작업<br>- `message`: 사용자 발화 전송<br>- `webLink`: 웹 링크 열기<br>- `phone`: 전화 걸기, PC 카카오톡에서는 미노출, 모바일 환경에서 말풍선 동작 확인하는 것을 권장<br>- `share`: 메시지 공유<br>- `operator`: 채널 1:1 채팅이나 상담톡으로 상담사 연결<br>- `invite`: 봇을 채팅방에 초대<br>- `mention`: 입력창에 봇 멘션 입력<br>- `inviteMember`: 현재 채팅방에 멤버 초대<br>- `settings`: 봇 설정 페이지 열기<br>- `guide`: 봇 도움말 페이지 열기 | O |
| `label` | `String` | 버튼 문구(최대: 14자, 가로 배열 2개인 경우 8자) | O |
| `messageText` | `String` | 사용자 발화로 전송할 텍스트<br>**중요**: `action`이 `message`인 경우 필수 | X |
| `webLinkUrl` | `String` | 버튼 선택 시 이동할 URL<br>버튼 선택 시 `botGroupKey`, `botUserKey`가 쿼리 파라미터로 추가 전달됨 (단, PC 미로그인 시 `botUserKey`는 전달되지 않음, 채널채팅 제외)<br>**중요**: `action`이 `webLink`인 경우 필수 | X |
| `phoneNumber` | `String` | 선택 시 전화할 전화번호, PC 카카오톡에서는 미노출<br>**중요**: `action`이 `phone`인 경우 필수 | X |
| `extra` | `JSON` | `message` 액션으로 블록 호출 시 스킬 서버에 추가 전달하는 정보(키는 String, 값은 Object 형식) | X |

### Profile

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `nickname` | `String` | 프로필 이름 | O |
| `imageUrl` | `String` | 프로필 이미지 URL<br>180x180 픽셀 권장 | O |

### Link

`Thumbnail` , `ListItem` 선택 시 `botGroupKey`, `botUserKey`가 쿼리 파라미터로 추가 전달됨 (단, PC 미로그인 시 `botUserKey`는 전달되지 않음, 채널채팅 제외)

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `mobile` | `String` | 모바일 웹 URL | X |
| `pc` | `String` | PC 웹 URL | X |
| `web` | `String` | 모든 기기 공통 웹 URL | X |

### Thumbnail

| 이름 | 타입 | 설명 | 필수 |
| :--- | :--- | :--- | :--- |
| `imageUrl` | `String` | 이미지 URL, 캐러셀 내 모든 이미지는 정사각형(1:1) 또는 와이드형(2:1)으로 통일 필요 | O |
| `link` | `Link` | 선택 시 이동할 플랫폼별 링크 정보<br>- PC 환경 우선순위: `pc` → `web`<br>- 모바일 환경 우선순위: `mobile` → `web` | X |
| `fixedRatio` | `Boolean` | 이미지 비율 고정 여부<br>- `true`: 1:1 비율 유지<br>- `false`: 2:1 비율로 가운데 크롭(기본값) | X |
| `altText` | `String` | 스크린 리더 대체 텍스트(최대: 50자) | X |

