from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from api.data_api import fetch_and_refine_stores
from api.kakao_api import get_coords_from_address
from services.claud_service import ask_claude_to_pick_stores
from services.planner import calculate_timeline

# 1. FastAPI 웹 서버 앱 객체 생성
app = FastAPI(
    title="소상공인 상생 로컬 여행 플래너 API",
    description="출발지와 목적지를 기반으로 주변 소상공인 상권을 연계한 맞춤형 일정을 생성합니다."
)


# 2. 웹 브라우저(클라이언트)에서 던져줄 데이터 규격 정의 (출발지 데이터 추가!)
class PlannerRequest(BaseModel):
    start_address: str = "서울특별시 강서구 화곡로 168 (화곡역)"
    dest_address: str = "서울특별시 강서구 공항대로 260 (이대서울병원)"
    start_time: str = "13:00"


@app.get("/")
def read_root():
    return {"message": "로컬 여행 플래너 웹 서버가 정상 작동 중입니다. /docs 로 접속해 보세요!"}


# 3. 실제 스케줄을 짜주는 POST API 엔드포인트
@app.post("/generate-plan")
def generate_plan(request: PlannerRequest):
    try:
        # [Step 0] 두 주소 텍스트를 변환하면서 카카오가 찾은 진짜 이름(place_name)도 받아옵니다.
        start_lon, start_lat, kakao_start_name = get_coords_from_address(request.start_address)
        dest_lon, dest_lat, kakao_dest_name = get_coords_from_address(request.dest_address)

        if not start_lon or not dest_lon:
            raise HTTPException(
                status_code=400,
                detail="출발지 주소 또는 도착지 주소를 인식할 수 없습니다. 정확한 주소를 입력해 주세요."
            )

        # 🔥 [수정] 꼼수 쓰던 자르기 코드 대신 카카오가 준 진짜 신뢰할 수 있는 이름을 사용합니다.
        # 만약 카카오 이름이 비어있을 때를 대비한 최소한의 폴백만 유지
        short_start_name = kakao_start_name if kakao_start_name else "출발지"
        short_dest_name = kakao_dest_name if kakao_dest_name else "목적지"

        # [Step 1] 변환된 '도착지 좌표' 주변 반경 1.5km 내의 소상공인 점포들 수집
        raw_food_candidates = fetch_and_refine_stores(
            cx=dest_lon, cy=dest_lat, radius=1500, inds_lcls_cd="I2", num_of_rows=15
        )
        raw_retail_candidates = fetch_and_refine_stores(
            cx=dest_lon, cy=dest_lat, radius=1500, inds_lcls_cd="G2", num_of_rows=15
        )

        # 업종 필터링 및 카페/식당 분리
        exclude_keywords = ["수산", "도매", "철물", "인테리어", "부품", "건재", "부동산"]
        food_stores = [
            s for s in raw_food_candidates
            if "카페" not in s["category"] and "커피" not in s["category"]
               and not any(k in s["name"] for k in exclude_keywords)
        ]
        cafe_stores = [
            s for s in raw_food_candidates
            if ("카페" in s["category"] or "커피" in s["category"])
               and not any(k in s["name"] for k in exclude_keywords)
        ]
        retail_stores = [
            s for s in raw_retail_candidates
            if not any(k in s["name"] for k in exclude_keywords)
        ]

        if not food_stores or not cafe_stores or not retail_stores:
            raise HTTPException(status_code=404, detail="목적지 주변 소상공인 점포 데이터가 부족합니다.")

        # [Step 2] Claude AI 큐레이팅 요청
        ai_choice = ask_claude_to_pick_stores(short_dest_name, food_stores + cafe_stores, retail_stores)

        f_idx = ai_choice.get("selected_food_idx", 0) % len(food_stores)
        c_idx = ai_choice.get("selected_cafe_idx", 0) % len(cafe_stores)
        r_idx = ai_choice.get("selected_retail_idx", 0) % len(retail_stores)

        selected_food = food_stores[f_idx]
        selected_cafe = cafe_stores[c_idx]
        selected_retail = retail_stores[r_idx]

        # [Step 3] 최종 타임라인 조립
        final_timeline = calculate_timeline(
            start_time_str=request.start_time,
            start_name=short_start_name,
            start_lon=start_lon,
            start_lat=start_lat,
            dest_name=short_dest_name,
            dest_lon=dest_lon,
            dest_lat=dest_lat,
            selected_retail=selected_retail,
            selected_food=selected_food,
            selected_cafe=selected_cafe
        )

        return {
            "status": 200,
            "meta": {
                "start_place": short_start_name,
                "destination": short_dest_name
            },
            "course_concept": ai_choice.get("course_concept", "로컬 상권 탐방 코스"),
            "timeline": final_timeline
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))