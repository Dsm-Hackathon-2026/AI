import requests
from config import KAKAO_HEADERS, KAKAO_REST_API_KEY


def get_driving_duration_minutes(origin_lon, origin_lat, dest_lon, dest_lat):
    """
    카카오 내비(길찾기) API를 사용하여 출발지에서 목적지까지의 차량 이동 시간(분)을 계산합니다.
    """
    url = "https://apis-navi.kakaomobility.com/v1/directions"

    params = {
        "origin": f"{origin_lon},{origin_lat}",
        "destination": f"{dest_lon},{dest_lat}",
        "priority": "RECOMMEND"
    }

    try:
        response = requests.get(url, headers=KAKAO_HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 카카오 응답 구조에서 첫 번째 추천 경로의 시간(초 단위) 추출
            routes = data.get("routes", [])
            if routes:
                duration_seconds = routes[0].get("summary", {}).get("duration", 0)
                # 초 단위를 분 단위로 반환 (반올림)
                return round(duration_seconds / 60)
        else:
            print(f"[Kakao API Error] Status Code: {response.status_code}")

    except Exception as e:
        print(f"[Kakao API Exception] {e}")

    return 15  # 에러 발생 시 기본값 15분으로 대체(안전장치)


def get_coords_from_address(address_name):
    """
    지명이나 상세주소 텍스트를 받아 카카오 로컬 API로
    (위도, 경도, 실제 장소명)을 반환합니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": address_name, "size": 1}

    try:
        response = requests.get(url, headers=headers, params=params).json()
        if response.get("documents"):
            doc = response["documents"][0]
            # x는 경도(lon), y는 위도(lat), place_name은 카카오가 찾은 실제 이름
            return float(doc["x"]), float(doc["y"]), doc["place_name"]
    except Exception as e:
        print(f"[Kakao Geo Error] {e}")
    return None, None, None