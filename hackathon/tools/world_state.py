import json
from typing import Any

from agents.tools import register_tool
from hackathon.constitution import load_world_state, save_world_state


@register_tool(
    name="get_world_state",
    description="가상 도시의 현재 누적 상태(구역, 인물/시설, 규칙, 사건 타임라인, 확정 사실, 가설, 지표)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "description": "조회할 섹션 키 (all, zones, entities, rules, events, facts, hypotheses, metrics 중 선택. 기본값 all)",
            },
        },
    },
)
def get_world_state(section: str = "all") -> str:
    state = load_world_state()
    if section and section != "all" and section in state:
        return json.dumps({section: state[section]}, ensure_ascii=False, indent=2)
    return json.dumps(state, ensure_ascii=False, indent=2)


@register_tool(
    name="update_world_state",
    description=(
        "새로 파악된 가상 도시의 단서, 규칙, 사건, 확정 사실(facts), 가설(hypotheses), 구역(zones), 지표(metrics)를 "
        "hackathon/world_state.json에 누적 기록하거나 갱신합니다."
    ),
    parameters={
        "type": "object",
        "properties": {
            "city_name": {
                "type": "string",
                "description": "파악된 가상 도시 이름 (변경 시에만 입력)",
            },
            "scenario_summary": {
                "type": "string",
                "description": "현재 시나리오 또는 문제 요약 (변경 시에만 입력)",
            },
            "add_rules": {
                "type": "array",
                "items": {"type": "string"},
                "description": "새로 확인된 도시 규칙 또는 제약 조건 목록",
            },
            "add_events": {
                "type": "array",
                "items": {"type": "string"},
                "description": "새로 파악된 사건(시간/장소/내용 포함) 목록",
            },
            "add_facts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "교차 검증이 완료된 확정 사실 목록",
            },
            "add_hypotheses": {
                "type": "array",
                "items": {"type": "string"},
                "description": "단서가 불완전하여 추가 검증이 필요한 가설/관계자 미검증 발언 목록",
            },
            "add_data_quality_issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "데이터 수집·검증·정제 과정에서 발견된 오류, 중복, 결측치, 단위 불일치 내역",
            },
            "zones_patch": {
                "type": "object",
                "description": "추가/수정할 구역(zone) 정보 사전",
            },
            "entities_patch": {
                "type": "object",
                "description": "추가/수정할 인물·기관·시설 정보 사전",
            },
            "metrics_patch": {
                "type": "object",
                "description": "추가/수정할 핵심 수치/지표 사전",
            },
        },
    },
)
def update_world_state(
    city_name: str | None = None,
    scenario_summary: str | None = None,
    add_rules: list[str] | None = None,
    add_events: list[str] | None = None,
    add_facts: list[str] | None = None,
    add_hypotheses: list[str] | None = None,
    add_data_quality_issues: list[str] | None = None,
    zones_patch: dict[str, Any] | None = None,
    entities_patch: dict[str, Any] | None = None,
    metrics_patch: dict[str, Any] | None = None,
) -> str:
    state = load_world_state()

    if city_name:
        state["city_name"] = city_name
    if scenario_summary:
        state["scenario_summary"] = scenario_summary

    for key, items in (
        ("rules", add_rules),
        ("events", add_events),
        ("facts", add_facts),
        ("hypotheses", add_hypotheses),
        ("data_quality_issues", add_data_quality_issues),
    ):
        if items:
            existing: list[Any] = list(state.get(key) or [])
            for item in items:
                if item and item not in existing:
                    existing.append(item)
            state[key] = existing

    for key, patch in (
        ("zones", zones_patch),
        ("entities", entities_patch),
        ("metrics", metrics_patch),
    ):
        if isinstance(patch, dict) and patch:
            current = dict(state.get(key) or {})
            current.update(patch)
            state[key] = current

    saved = save_world_state(state)
    return "world_state.json 갱신 완료:\n" + json.dumps(saved, ensure_ascii=False, indent=2)

