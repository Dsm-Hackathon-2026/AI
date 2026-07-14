import requests
from config import DATA_API_KEY


def fetch_and_refine_stores(cx, cy, radius=500, inds_lcls_cd="I2", num_of_rows=10):
    """
    소상공인 API를 호출하여 지정된 반경 내의 상가 정보를 가져온 후 핵심 정보만 정제합니다.
    - inds_lcls_cd: 'I2' (음식점/카페), 'G2' (소매/옷가게/소품샵)
    """
    url = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius"

    params = {
        "ServiceKey": DATA_API_KEY,
        "radius": str(radius),
        "cx": str(cx),
        "cy": str(cy),
        "indsLclsCd": inds_lcls_cd,
        "numOfRows": str(num_of_rows),
        "type": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        # 공공데이터포털 에러 대처를 위해 status_code 외에 실제 데이터 검증
        if response.status_code != 200:
            print(f"[Data API Error] Status Code: {response.status_code}")
            return []

        data = response.json()

        # NODATA_ERROR 등의 처리
        result_code = data.get("header", {}).get("resultCode")
        if result_code != "00":
            print(f"[Data API Warning] Result Code: {result_code}, Msg: {data.get('header', {}).get('resultMsg')}")
            return []

        items = data.get("body", {}).get("items", [])
        refined_list = []

        for item in items:
            # Claude 토큰 절약 및 카카오 길찾기를 위한 알짜 정보 패킹
            refined_store = {
                "name": item.get("bizesNm"),  # 상호명
                "category": item.get("indsSclsNm"),  # 소분류명 (예: 복 요리 전문, 커피점/카페)
                "address": item.get("rdnmAdr"),  # 도로명 주소
                "lon": item.get("lon"),  # 경도
                "lat": item.get("lat")  # 위도
            }
            refined_list.append(refined_store)

        return refined_list

    except Exception as e:
        print(f"[Data API Exception] {e}")
        return []