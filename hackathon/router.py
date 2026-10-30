import json
import logging
import re
from typing import Literal

import httpx

from hackathon.constitution import load_world_state
from hackathon.tools.solution_bank import SOLUTIONS_DIR, list_solution_files

log = logging.getLogger("hackathon.router")

RouteDecision = Literal["SOLUTION_HIT", "SIMPLE", "COMPLEX"]

# 다중 제약·수리 최적화·데이터 정제·복합 추론을 시사하는 고난도 시그널 정규식
_COMPLEX_KEYWORDS_RE = re.compile(
    r"(최적|최소|최대|경로|스케줄|배치|시뮬레이션|모든\s*경우|조합\s*업무|비교\s*분석|"
    r"모순|범인|진범|진실|거짓|트레이드오프|우선순위|예산\s*배분|동시\s*만족|해결책|개선안|방안|원인|"
    r"정제|검증|오류|이상치|결측|불일치|정산|수급\s*예측|물류)",
    re.IGNORECASE,
)


def match_preverified_solution(user_message: str) -> str | None:
    """
    근거 1 (사전 풀이 대조): hackathon/solutions/ 에 저장된 검증 완료 해답의 제목/파일명 토큰이
    질문과 일치하면 해당 해답 원문을 즉시 반환합니다.
    """
    files = list_solution_files()
    if not files:
        return None

    normalized_msg = user_message.lower()
    matched_contents: list[str] = []

    for rel_path in files:
        full_path = SOLUTIONS_DIR / rel_path
        if not full_path.is_file():
            continue
        stem_tokens = [
            tok for tok in re.split(r"[_\-\s./]+", full_path.stem.lower()) if len(tok) >= 2
        ]
        content = full_path.read_text(encoding="utf-8", errors="replace").strip()
        first_line = content.splitlines()[0].lstrip("# ").strip().lower() if content else ""
        title_tokens = [tok for tok in re.split(r"\s+", first_line) if len(tok) >= 2]

        all_tokens = set(stem_tokens + title_tokens)
        if all_tokens and any(tok in normalized_msg for tok in all_tokens):
            matched_contents.append(f"[{rel_path}]\n{content}")

    if matched_contents:
        return "\n\n---\n\n".join(matched_contents)
    return None


def evaluate_state_coverage(user_message: str) -> tuple[RouteDecision | None, str]:
    """
    근거 2 (지식베이스 커버리지 및 미해결 가설 대조):
    단순 문장 길이가 아니라 현재 world_state.json 에 확정된 사실(facts/metrics)로 답할 수 있는지,
    아니면 아직 미해결 가설(hypotheses)이거나 다중 제약 연산이 필요한지를 대조합니다.
    """
    state = load_world_state()
    routing_mode = str(state.get("routing_mode", "auto")).lower()
    if routing_mode == "always_heavy":
        return "COMPLEX", "routing_mode=always_heavy 강제 설정"
    if routing_mode == "always_local":
        return "SIMPLE", "routing_mode=always_local 강제 설정"

    text = user_message.strip()

    # 1. 질문의 핵심 대상이 아직 '미해결 가설(hypotheses)'에 머물러 있다면 짧은 질문이어도 COMPLEX로 분류
    hypotheses = [str(h) for h in (state.get("hypotheses") or [])]
    for hyp in hypotheses:
        hyp_tokens = [t for t in re.split(r"[\s,./()]+", hyp) if len(t) >= 2]
        if hyp_tokens and sum(1 for t in hyp_tokens if t in text) >= 2:
            return "COMPLEX", f"미해결 가설(hypotheses) 관련 질문 감지: '{hyp[:40]}'"

    # 2. 고난도 최적화/추론 키워드가 포함되면서 아직 solutions/ 에 없는 경우 COMPLEX
    complex_matches = _COMPLEX_KEYWORDS_RE.findall(text)
    if len(complex_matches) >= 2 or (len(complex_matches) >= 1 and len(text) >= 50):
        return (
            "COMPLEX",
            f"사전 풀이에 없는 복합 추론/최적화 키워드 감지 ({', '.join(set(complex_matches))})",
        )

    # 3. 조건절·복수 의문문이 결합된 신규 시나리오 질문
    if len(text) >= 140 or text.count("?") >= 2:
        return "COMPLEX", "다중 조건/복수 질문이 포함된 신규 시나리오"

    return None, ""


async def classify_with_context_llm(
    user_message: str,
    timeout: float = 4.0,
) -> tuple[RouteDecision, str]:
    """
    근거 3 (컨텍스트 기반 로컬 모델 자기 판별, think=False):
    로컬 qwen3.8에게 질문만 주는 것이 아니라 '현재 world_state.json 보유 현황'을 함께 제시하여,
    이미 보유한 사실(facts/metrics) 조회만으로 답할 수 있는지(SIMPLE) vs 새로운 추론/시뮬레이션이 필요한지(COMPLEX) 판별합니다.
    """
    state = load_world_state()
    compact_state = {
        "city_name": state.get("city_name"),
        "facts_count": len(state.get("facts") or []),
        "facts_preview": (state.get("facts") or [])[:10],
        "hypotheses_preview": (state.get("hypotheses") or [])[:5],
        "metrics_keys": list((state.get("metrics") or {}).keys()),
        "solutions_files": list_solution_files(),
    }
    classifier_prompt = (
        "당신은 질문 라우터입니다. 아래 [현재 보유 지식 상태]만으로 사용자 질문에 즉시 답할 수 있는지 판별하세요.\n"
        "- SIMPLE: 보유 지식(facts, metrics)의 단순 조회/요약이거나 1단계 간단한 확인으로 즉시 답변 가능한 경우\n"
        "- COMPLEX: 보유 지식에 확정된 답이 없어 다중 제약 최적화, 새로운 추론, 데이터 교차 검증이 필요한 경우\n\n"
        f"[현재 보유 지식 상태]\n{json.dumps(compact_state, ensure_ascii=False)}\n\n"
        "반드시 첫 단어는 SIMPLE 또는 COMPLEX로 시작하고 한 줄로 이유를 적으세요."
    )
    from api.config import OLLAMA_BASE_URL, OLLAMA_MODEL

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": classifier_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "think": False,
        "options": {"num_predict": 30, "temperature": 0.0},
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat", json=payload)
            resp.raise_for_status()
            content = (resp.json().get("message") or {}).get("content", "").strip()
            if content.upper().startswith("COMPLEX") or "COMPLEX" in content.upper()[:15]:
                return "COMPLEX", f"로컬 모델 컨텍스트 대조 판정: {content}"
            return "SIMPLE", f"로컬 모델 컨텍스트 대조 판정: {content}"
    except Exception as exc:
        log.debug("Context LLM classifier skipped (%s)", exc)
        if _COMPLEX_KEYWORDS_RE.search(user_message):
            return "COMPLEX", "고난도 추론 키워드 포함 (폴백 판정)"
        return "SIMPLE", "기본 로컬 처리"


async def route_user_message(user_message: str) -> tuple[RouteDecision, str | None]:
    """
    사용자 자연어 질문을 받아:
    - SOLUTION_HIT: (SOLUTION_HIT, 매칭된 사전 풀이 본문)
    - COMPLEX: (COMPLEX, 구체적인 위임 판정 사유)
    - SIMPLE: (SIMPLE, None)
    을 반환합니다.
    """
    solution_hit = match_preverified_solution(user_message)
    if solution_hit is not None:
        log.info("Router decision: SOLUTION_HIT")
        return "SOLUTION_HIT", solution_hit

    state_decision, reason = evaluate_state_coverage(user_message)
    if state_decision is not None:
        log.info("Router decision (state_coverage): %s (%s)", state_decision, reason)
        return state_decision, reason if state_decision == "COMPLEX" else None

    llm_decision, llm_reason = await classify_with_context_llm(user_message)
    log.info("Router decision (context_llm): %s (%s)", llm_decision, llm_reason)
    return llm_decision, llm_reason if llm_decision == "COMPLEX" else None
