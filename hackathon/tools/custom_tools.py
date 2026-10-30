"""
대회 당일 공개되는 가상 도시 전용 도구를 추가하는 모듈입니다.
@register_tool 데코레이터를 붙이면 OllamaClient에 자동으로 등록됩니다.
"""

# 예시:
# from agents.tools import register_tool
#
# @register_tool(
#     name="simulate_city_route",
#     description="구역 간 이동 시간과 통행 제약을 시뮬레이션합니다.",
#     parameters={
#         "type": "object",
#         "properties": {
#             "origin": {"type": "string"},
#             "destination": {"type": "string"},
#         },
#         "required": ["origin", "destination"],
#     },
# )
# def simulate_city_route(origin: str, destination: str) -> str:
#     return f"{origin} -> {destination} 최적 경로 계산 결과"

