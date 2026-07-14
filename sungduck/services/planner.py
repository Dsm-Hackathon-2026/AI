from datetime import datetime, timedelta
from api.kakao_api import get_driving_duration_minutes


# 1. 매개변수에 start_name, start_lon, start_lat를 추가합니다.
def calculate_timeline(start_time_str, start_name, start_address, start_lon, start_lat,
                       dest_name, dest_address, dest_lon, dest_lat,
                       selected_retail, selected_food, selected_cafe):
    """
    각 장소의 체류 시간과 카카오 길찾기 API의 이동 시간을 조합하여
    최종 타임라인 일정표를 조립합니다. (출발지부터 목적지 이동 시간 포함)
    """
    # 시작 시간 설정 (예: "13:00" -> datetime 객체로 변환)
    current_time = datetime.strptime(start_time_str, "%H:%M")
    timeline = []

    # [0단계] 출발지 -> 메인 목적지 이동 (★ 이 부분이 누락되어 있었습니다!)
    drive_to_dest = get_driving_duration_minutes(start_lon, start_lat, dest_lon, dest_lat)

    # 만약 카카오 API 오류 등으로 None이나 0이 올 경우를 대비한 최소 방어값 (예: 5분)
    if not drive_to_dest or drive_to_dest <= 0:
        drive_to_dest = 15

    dest_arrival_time = current_time + timedelta(minutes=drive_to_dest)

    # 타임라인에 첫 이동 정보 기록
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {dest_arrival_time.strftime('%H:%M')}",
        "place": start_name,
        "address": start_address,
        "activity": f"카카오 길찾기 기준 실제 이동 시간 약 {drive_to_dest}분 소요",
        "cx": start_lon,
        "cy": start_lat,
    })
    current_time = dest_arrival_time

    # [1단계] 메인 목적지 일정 (체류 2시간 가정)
    dest_duration = 120
    dest_end_time = current_time + timedelta(minutes=dest_duration)
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {dest_end_time.strftime('%H:%M')}",
        "place": dest_name,
        "address": dest_address,
        "activity": "메인 일정 수행",
        "cx": dest_lon,
        "cy": dest_lat
    })
    current_time = dest_end_time

    # [2단계] 목적지 -> 소상공인 쇼핑 장소 이동 및 쇼핑 (체류 1시간)
    drive_to_retail = get_driving_duration_minutes(dest_lon, dest_lat, selected_retail["lon"], selected_retail["lat"])
    current_time += timedelta(minutes=drive_to_retail)

    retail_duration = 60
    retail_end_time = current_time + timedelta(minutes=retail_duration)
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {retail_end_time.strftime('%H:%M')}",
        "place": f"{selected_retail['name']} ({selected_retail['category']})",
        "address": selected_retail["address"],
        "activity": f"이동({drive_to_retail}분) 후 소품샵/옷가게 구경 및 가치 소비",
        "cx": float(selected_retail["lon"]),
        "cy": float(selected_retail["lat"])
    })
    current_time = retail_end_time

    # [3단계] 쇼핑 -> 소상공인 식당 이동 및 식사 (체류 1시간)
    drive_to_food = get_driving_duration_minutes(selected_retail["lon"], selected_retail["lat"], selected_food["lon"],
                                                 selected_food["lat"])
    current_time += timedelta(minutes=drive_to_food)

    food_duration = 60
    food_end_time = current_time + timedelta(minutes=food_duration)
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {food_end_time.strftime('%H:%M')}",
        "place": f"{selected_food['name']} ({selected_food['category']})",
        "address": selected_food["address"],
        "activity": f"이동({drive_to_food}분) 후 지역 맛집에서 맛있는 식사",
        "cx": float(selected_food["lon"]),
        "cy": float(selected_food["lat"])
    })
    current_time = food_end_time

    # [4단계] 식당 -> 소상공인 카페 이동 및 휴식 (체류 1시간 30분)
    drive_to_cafe = get_driving_duration_minutes(selected_food["lon"], selected_food["lat"], selected_cafe["lon"],
                                                 selected_cafe["lat"])
    current_time += timedelta(minutes=drive_to_cafe)

    cafe_duration = 90
    cafe_end_time = current_time + timedelta(minutes=cafe_duration)
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {cafe_end_time.strftime('%H:%M')}",
        "place": f"{selected_cafe['name']} ({selected_cafe['category']})",
        "address": selected_cafe["address"],
        "activity": f"이동({drive_to_cafe}분) 후 감성 로컬 카페에서 디저트 및 티타임",
        "cx": float(selected_cafe["lon"]),
        "cy": float(selected_cafe["lat"])
    })

    return timeline