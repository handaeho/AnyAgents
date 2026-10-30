import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
KAKAO_API_URL: str = os.getenv("KAKAO_API_URL", "https://kapi.kakao.com")
KAKAO_GW_URL: str = os.getenv("KAKAO_GW_URL", "wss://bot-gateway.kakao.com/gateway")
ENABLE_GATEWAY: bool = os.getenv("ENABLE_GATEWAY", "true").lower() in ("1", "true", "yes")

