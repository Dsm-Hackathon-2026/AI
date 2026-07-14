import json
import anthropic
from config import CLAUDE_API_KEY


def ask_claude_to_pick_stores(destination_name, food_stores, retail_stores):
    """
    소상공인 후보 목록을 Claude에게 제공하고 컨셉에 맞는 최적의 식당 1곳, 카페 1곳, 쇼핑 1곳을 픽하게 합니다.
    """
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    # 후보 데이터를 Claude가 읽기 좋은 텍스트 덩어리로 변환
    food_candidates_text = ""
    for idx, s in enumerate(food_stores):
        food_candidates_text += f"[{idx}] 이름: {s['name']}, 분류: {s['category']}, 주소: {s['address']}\n"

    retail_candidates_text = ""
    for idx, s in enumerate(retail_stores):
        retail_candidates_text += f"[{idx}] 이름: {s['name']}, 분류: {s['category']}, 주소: {s['address']}\n"

    system_prompt = (
        "너는 지역 골목상권과 소상공인을 활성화하는 전문 로컬 여행 가이드 겸 큐레이터야.\n"
        "제공된 소상공인 가게 후보 리스트 중에서 사용자의 메인 목적지와 가장 조화롭고 매력적인 코스가 될 수 있도록\n"
        "딱 [식당 1곳], [카페 1곳], [소매/쇼핑 1곳]을 골라줘.\n"
        "응답은 반드시 아래 지정된 JSON 형식으로만 해야 해. 다른 부연 설명이나 인사말은 절대로 하지 마.\n\n"
        "{\n"
        '  "selected_food_idx": 선택한 식당의 인덱스 번호(숫자),\n'
        '  "selected_cafe_idx": 선택한 카페의 인덱스 번호(숫자),\n'
        '  "selected_retail_idx": 선택한 쇼핑 장소의 인덱스 번호(숫자),\n'
        '  "course_concept": "이번 로컬 여행 코스의 테마/컨셉 설명 (한 줄)"\n'
        "}"
    )

    user_content = (
        f"메인 목적지: {destination_name}\n\n"
        f"== [음식점/카페 후보 리스트] ==\n{food_candidates_text}\n"
        f"== [소매/쇼핑 점포 후보 리스트] ==\n{retail_candidates_text}\n"
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-5",  # 최신 하이엔드 모델 기준
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )

        # 응답 텍스트를 JSON으로 파싱
        response_text = "".join([block.text for block in response.content if block.type == "text"]).strip()

        # 2. JSON 문자열만 정교하게 솎아내기 ({ } 괄호 안쪽만 추출)
        if "{" in response_text and "}" in response_text:
            start_idx = response_text.index("{")
            end_idx = response_text.rindex("}") + 1
            response_text = response_text[start_idx:end_idx]

        return json.loads(response_text)
    except Exception as e:
        print(f"[Claude Service Error] {e}")
        # 에러 발생 시 기본 첫 번째 아이템들을 선택하는 폴백(Fallback) 구조
        return {"selected_food_idx": 0, "selected_cafe_idx": 1, "selected_retail_idx": 0,
                "course_concept": "로컬 상권 탐방 코스"}