# hackathon/queue (실시간 Codex / Gemini 위임 큐)

- `inbox.md`: 카카오톡 챗봇(`qwen3.8` 또는 `/위임` 명령)이 고난도 문제를 수신했을 때 자동 생성하는 요청서입니다.
- `outbox.md`: VS Code의 Codex 또는 Gemini가 `inbox.md`의 문제를 풀고 최종 답변을 작성하는 파일입니다. 작성 즉시 챗봇이 감지하여 카카오톡으로 발송합니다.
- `status.json`: 현재 위임 작업의 상태(`idle`, `pending`, `completed`) 및 발송 대상 키(`botUserKey`, `botGroupKey`)를 기록합니다.

