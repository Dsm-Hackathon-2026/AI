# API 키를 한곳에서 관리합니다. (추후 .env 파일로 격리하기 좋습니다.)
import os

KAKAO_REST_API_KEY = os.environ["KAKAO_REST_API_KEY"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
DATA_API_KEY = os.environ["DATA_API_KEY"]

KAKAO_HEADERS = {
    "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
}
