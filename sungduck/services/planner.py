from datetime import datetime, timedelta
from api.kakao_api import get_driving_duration_minutes


def calculate_timeline(start_time_str, start_name, start_address, start_lon, start_lat,
                       dest_name, dest_address, dest_lon, dest_lat,
                       selected_retail, selected_food, selected_cafe):
    """
    [동선 전면 수정]
    출발지 -> 소상공인 가게들(쇼핑->식당->카페) -> 최종 목적지 순서로
    이동 시간과 체류 시간을 한 줄로 이어지게 계산하여 타임라인을 조립합니다.
    """
    current_time = datetime.strptime(start_time_str, "%H:%M")
    timeline = []

    # =========================================================================
    # [1단계] 출발지 -> 소상공인 쇼핑 장소로 이동 및 쇼핑 (체류 1시간)
    # =========================================================================
    # ★ 출발지 좌표(start_lon, start_lat)에서 쇼핑몰 좌표로의 이동 시간을 구합니다.
    drive_to_retail = get_driving_duration_minutes(start_lon, start_lat, selected_retail["lon"], selected_retail["lat"])
    if not drive_to_retail or drive_to_retail <= 0:
        drive_to_retail = 15

    retail_arrival_time = current_time + timedelta(minutes=drive_to_retail)

    # 타임라인에 첫 출발 정보 기록
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {retail_arrival_time.strftime('%H:%M')}",
        "place": start_name,
        "address": start_address,
        "activity": f"카카오 길찾기 기준 실제 이동 시간 약 {drive_to_retail}분 소요",
        "longitude": float(start_lon),
        "latitude": float(start_lat),
    })
    current_time = retail_arrival_time

    # 쇼핑 수행 (체류 1시간)
    retail_duration = 60
    retail_end_time = current_time + timedelta(minutes=retail_duration)
    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {retail_end_time.strftime('%H:%M')}",
        "place": f"{selected_retail['name']} ({selected_retail['category']})",
        "address": selected_retail["address"],
        "activity": "소품샵/옷가게 구경 및 로컬 가치 소비",
        "longitude": float(selected_retail["lon"]),
        "latitude": float(selected_retail["lat"])
    })
    current_time = retail_end_time

    # =========================================================================
    # [2단계] 쇼핑 -> 소상공인 식당 이동 및 식사 (체류 1시간)
    # =========================================================================
    # ★ 쇼핑몰에서 식당으로의 이동 시간을 구합니다.
    drive_to_food = get_driving_duration_minutes(selected_retail["lon"], selected_retail["lat"], selected_food["lon"],
                                                 selected_food["lat"])
    if not drive_to_food or drive_to_food <= 0:
        drive_to_food = 15

    current_time += timedelta(minutes=drive_to_food)

    food_duration = 60
    food_end_time = current_time + timedelta(minutes=food_duration)
    timeline.append({
        "time": f"{(current_time - timedelta(minutes=drive_to_food)).strftime('%H:%M')} ~ {food_end_time.strftime('%H:%M')}",
        "place": f"{selected_food['name']} ({selected_food['category']})",
        "address": selected_food["address"],
        "activity": f"이동({drive_to_food}분) 후 지역 맛집에서 맛있는 식사",
        "longitude": float(selected_food["lon"]),
        "latitude": float(selected_food["lat"])
    })
    current_time = food_end_time

    # =========================================================================
    # [3단계] 식당 -> 소상공인 카페 이동 및 휴식 (체류 1시간 30분)
    # =========================================================================
    # ★ 식당에서 카페로의 이동 시간을 구합니다.
    drive_to_cafe = get_driving_duration_minutes(selected_food["lon"], selected_food["lat"], selected_cafe["lon"],
                                                 selected_cafe["lat"])
    if not drive_to_cafe or drive_to_cafe <= 0:
        drive_to_cafe = 15

    current_time += timedelta(minutes=drive_to_cafe)

    cafe_duration = 90
    cafe_end_time = current_time + timedelta(minutes=cafe_duration)
    timeline.append({
        "time": f"{(current_time - timedelta(minutes=drive_to_cafe)).strftime('%H:%M')} ~ {cafe_end_time.strftime('%H:%M')}",
        "place": f"{selected_cafe['name']} ({selected_cafe['category']})",
        "address": selected_cafe["address"],
        "activity": f"이동({drive_to_cafe}분) 후 감성 로컬 카페에서 디저트 및 티타임",
        "longitude": float(selected_cafe["lon"]),
        "latitude": float(selected_cafe["lat"])
    })
    current_time = cafe_end_time

    # =========================================================================
    # [4단계] 카페 -> 최종 목적지 이동 및 메인 일정 수행 (마무리)
    # =========================================================================
    # ★ 카페에서 최종 목적지(dest_lon, dest_lat)로의 이동 시간을 구합니다.
    drive_to_dest = get_driving_duration_minutes(selected_cafe["lon"], selected_cafe["lat"], dest_lon, dest_lat)
    if not drive_to_dest or drive_to_dest <= 0:
        drive_to_dest = 15

    current_time += timedelta(minutes=drive_to_dest)

    dest_duration = 120
    dest_end_time = current_time + timedelta(minutes=dest_duration)
    timeline.append({
        "time": f"{(current_time - timedelta(minutes=drive_to_dest)).strftime('%H:%M')} ~ {dest_end_time.strftime('%H:%M')}",
        "place": dest_name,
        "address": dest_address,
        "activity": f"이동({drive_to_dest}분) 후 최종 목적지 도착 및 메인 일정 수행",
        "longitude": float(dest_lon),
        "latitude": float(dest_lat)
    })

    return timeline


# services/planner.py 에 아래 함수를 새로 추가해 주세요. (기존 함수는 그대로 둡니다!)

def calculate_multi_timeline(start_time_str, start_name, start_address, start_lon, start_lat,
                             dest_info_list, selected_retail, selected_food, selected_cafe,
                             additional_stores):
    """
    [다중 목적지 전용]
    1. 출발지 -> 쇼핑 -> 식당 -> 카페 -> 첫 번째 목적지 (기존 3개 추천 동선 유지)
    2. 이후 목적지들이 있다면: 첫 번째 목적지 -> 추가 상점 -> 두 번째 목적지... 순으로 연장
    """
    current_time = datetime.strptime(start_time_str, "%H:%M")
    timeline = []

    first_dest = dest_info_list[0]

    # =========================================================================
    # [기본 동선] 출발지 ➔ 쇼핑 ➔ 식당 ➔ 카페 ➔ 첫 번째 목적지
    # =========================================================================

    # 1. 출발지 -> 쇼핑 장소 이동 및 쇼핑
    drive_to_retail = get_driving_duration_minutes(start_lon, start_lat, selected_retail["lon"], selected_retail["lat"])
    drive_to_retail = drive_to_retail if (drive_to_retail and drive_to_retail > 0) else 15
    retail_arrival_time = current_time + timedelta(minutes=drive_to_retail)

    timeline.append({
        "time": f"{current_time.strftime('%H:%M')} ~ {retail_arrival_time.strftime('%H:%M')}",
        "place": start_name,
        "address": start_address,
        "activity": f"이동 약 {drive_to_retail}분 소요",
        "longitude": float(start_lon),
        "latitude": float(start_lat),
    })
    current_time = retail_arrival_time + timedelta(minutes=60)  # 쇼핑 1시간 체류

    timeline.append({
        "time": f"{retail_arrival_time.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}",
        "place": f"{selected_retail['name']} ({selected_retail['category']})",
        "address": selected_retail["address"],
        "activity": "소품샵/옷가게 구경 및 로컬 가치 소비",
        "longitude": float(selected_retail["lon"]),
        "latitude": float(selected_retail["lat"])
    })

    # 2. 쇼핑 -> 식당 이동 및 식사
    drive_to_food = get_driving_duration_minutes(selected_retail["lon"], selected_retail["lat"], selected_food["lon"],
                                                 selected_food["lat"])
    drive_to_food = drive_to_food if (drive_to_food and drive_to_food > 0) else 15
    food_arrival_time = current_time + timedelta(minutes=drive_to_food)
    current_time = food_arrival_time + timedelta(minutes=60)  # 식사 1시간 체류

    timeline.append({
        "time": f"{food_arrival_time.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}",
        "place": f"{selected_food['name']} ({selected_food['category']})",
        "address": selected_food["address"],
        "activity": f"이동({drive_to_food}분) 후 지역 맛집에서 식사",
        "longitude": float(selected_food["lon"]),
        "latitude": float(selected_food["lat"])
    })

    # 3. 식당 -> 카페 이동 및 휴식
    drive_to_cafe = get_driving_duration_minutes(selected_food["lon"], selected_food["lat"], selected_cafe["lon"],
                                                 selected_cafe["lat"])
    drive_to_cafe = drive_to_cafe if (drive_to_cafe and drive_to_cafe > 0) else 15
    cafe_arrival_time = current_time + timedelta(minutes=drive_to_cafe)
    current_time = cafe_arrival_time + timedelta(minutes=90)  # 카페 1시간 30분 체류

    timeline.append({
        "time": f"{cafe_arrival_time.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}",
        "place": f"{selected_cafe['name']} ({selected_cafe['category']})",
        "address": selected_cafe["address"],
        "activity": f"이동({drive_to_cafe}분) 후 디저트 및 티타임",
        "longitude": float(selected_cafe["lon"]),
        "latitude": float(selected_cafe["lat"])
    })

    # 4. 카페 -> 첫 번째 목적지 이동 및 메인 일정 수행
    drive_to_dest = get_driving_duration_minutes(selected_cafe["lon"], selected_cafe["lat"], first_dest["lon"],
                                                 first_dest["lat"])
    drive_to_dest = drive_to_dest if (drive_to_dest and drive_to_dest > 0) else 15
    dest_arrival_time = current_time + timedelta(minutes=drive_to_dest)
    current_time = dest_arrival_time + timedelta(minutes=120)  # 첫 목적지 2시간 체류

    timeline.append({
        "time": f"{dest_arrival_time.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}",
        "place": first_dest["name"],
        "address": first_dest["address"],
        "activity": f"이동({drive_to_dest}분) 후 첫 번째 목적지 메인 일정 수행",
        "longitude": float(first_dest["lon"]),
        "latitude": float(first_dest["lat"])
    })

    # =========================================================================
    # [확장 동선] 두 번째 목적지부터 루프를 돌며 동선 연장
    # =========================================================================
    last_location = first_dest

    for idx, next_dest in enumerate(dest_info_list[1:]):
        store = additional_stores[idx]

        # 이전 목적지 ➔ 추가 상점 이동 및 체류 (1시간)
        drive_to_store = get_driving_duration_minutes(last_location["lon"], last_location["lat"], store["lon"],
                                                      store["lat"])
        drive_to_store = drive_to_store if (drive_to_store and drive_to_store > 0) else 15
        store_arrival_time = current_time + timedelta(minutes=drive_to_store)
        current_time = store_arrival_time + timedelta(minutes=60)

        timeline.append({
            "time": f"{store_arrival_time.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}",
            "place": f"{store['name']} ({store.get('category', '상점')})",
            "address": store["address"],
            "activity": f"이동({drive_to_store}분) 후 경유지 상권 방문 및 휴식",
            "longitude": float(store["lon"]),
            "latitude": float(store["lat"])
        })

        # 추가 상점 ➔ 다음 메인 목적지 이동 및 일정 수행 (2시간)
        drive_to_next_dest = get_driving_duration_minutes(store["lon"], store["lat"], next_dest["lon"],
                                                          next_dest["lat"])
        drive_to_next_dest = drive_to_next_dest if (drive_to_next_dest and drive_to_next_dest > 0) else 15
        next_dest_arrival_time = current_time + timedelta(minutes=drive_to_next_dest)
        current_time = next_dest_arrival_time + timedelta(minutes=120)

        timeline.append({
            "time": f"{next_dest_arrival_time.strftime('%H:%M')} ~ {current_time.strftime('%H:%M')}",
            "place": next_dest["name"],
            "address": next_dest["address"],
            "activity": f"이동({drive_to_next_dest}분) 후 목적지 일정 수행",
            "longitude": float(next_dest["lon"]),
            "latitude": float(next_dest["lat"])
        })

        last_location = next_dest

    return timeline