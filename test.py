import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ✅ API 키를 여기에 직접 작성
kakao_api_key = "c01caa2d92080c9d7a47b122970248a7"
tmap_api_key = "MSQEscmmjL6QqEvry9SJ47eodN5WnKD6R9kv5ie4"

print(kako_api_key, tmap_api_key)
# 주소 또는 키워드 → 좌표 변환 함수
def address_to_coord(address, kakao_api_key):
    # 1️⃣ 주소 검색 시도
    url_address = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
    params = {"query": address}

    response = requests.get(url_address, headers=headers, params=params).json()
    documents = response.get("documents", [])

    if documents:
        x = float(documents[0]["x"])
        y = float(documents[0]["y"])
        return x, y

    # 2️⃣ 주소 검색 실패 시 → 키워드 검색 fallback
    url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params_keyword = {"query": address}

    response_keyword = requests.get(url_keyword, headers=headers, params=params_keyword).json()
    documents_keyword = response_keyword.get("documents", [])

    if documents_keyword:
        x = float(documents_keyword[0]["x"])
        y = float(documents_keyword[0]["y"])
        st.info(f"⚠️ 주소 검색 실패 → 키워드 검색 결과 사용: {documents_keyword[0]['place_name']}")
        return x, y

    # 3️⃣ 완전히 실패
    return None, None

# TMAP 경로 요청 함수 + 요약 정보 반환
def get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key):
    if route_type == "자동차":
        url = "https://apis.openapi.sk.com/tmap/routes"
    else:  # 도보
        url = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&format=json"

    headers = {
        "appKey": tmap_api_key,
        "Content-Type": "application/json"
    }

    # 공통 payload
    payload = {
        "startX": str(start_x),
        "startY": str(start_y),
        "endX": str(end_x),
        "endY": str(end_y),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
    }

    # 보행자 옵션 추가 → startName, endName 반드시 추가
    if route_type == "도보":
        payload["startName"] = "출발지"
        payload["endName"] = "도착지"

    # 자동차 옵션 추가
    if route_type == "자동차":
        payload["searchOption"] = "0"

    # API 호출
    response = requests.post(url, headers=headers, json=payload).json()

    features = response.get("features", [])

    # 요약 정보 추출
    if features:
        properties = features[0].get("properties", {})
        summary = {
            "totalDistance": properties.get("totalDistance", 0),  # meter
            "totalTime": properties.get("totalTime", 0),          # second
            "totalFare": properties.get("totalFare", 0),          # 원
            "taxiFare": properties.get("taxiFare", 0)             # 원
        }
    else:
        summary = None

    return features, summary

# Streamlit UI 구성
st.title("🚗 여행지 경로 검색")

# 출발지/도착지 입력
st.header("🗺️ 경로 설정")
start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")
route_type = st.selectbox("경로 유형 선택", ["도보", "자동차"])  # 대중교통 삭제

# 경로 검색 버튼
if st.button("경로 검색"):
    start_x, start_y = address_to_coord(start_address, kakao_api_key)
    end_x, end_y = address_to_coord(end_address, kakao_api_key)

    if None in [start_x, start_y, end_x, end_y]:
        st.error("출발지 또는 도착지 주소를 찾을 수 없습니다.")
    else:
        st.success(f"출발지 좌표: ({start_y}, {start_x})\n도착지 좌표: ({end_y}, {end_x})")
        features, summary = get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key)

        # 지도 데이터 session state에 저장
        st.session_state['map_features'] = features
        st.session_state['start_coord'] = (start_y, start_x)
        st.session_state['end_coord'] = (end_y, end_x)
        st.session_state['route_summary'] = summary

# 지도 렌더링 + 요약 정보 표시
if 'map_features' in st.session_state:
    features = st.session_state['map_features']
    start_y, start_x = st.session_state['start_coord']
    end_y, end_x = st.session_state['end_coord']
    summary = st.session_state['route_summary']

    # 📋 경로 요약 정보 표시
    if summary:
        totalDistance_km = summary["totalDistance"] / 1000
        totalTime_min = summary["totalTime"] / 60
        st.subheader("📊 경로 요약 정보")
        st.write(f"**총 거리:** {totalDistance_km:.1f} km")
        st.write(f"**총 소요 시간:** {totalTime_min:.0f} 분")
        st.write(f"**총 요금:** {summary['totalFare']} 원")
        st.write(f"**예상 택시 요금:** {summary['taxiFare']} 원")

    # 지도 그리기
    m = folium.Map(location=[(start_y + end_y) / 2, (start_x + end_x) / 2], zoom_start=13)

    # 출발지/도착지 마커 추가
    folium.Marker([start_y, start_x], tooltip="출발지", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_y, end_x], tooltip="도착지", icon=folium.Icon(color='red')).add_to(m)

    # 경로 polyline 그리기
    route_line = []
    for feature in features:
        geometry = feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            coords = geometry.get("coordinates", [])
            for coord in coords:
                lon, lat = coord
                route_line.append((lat, lon))

    if route_line:
        folium.PolyLine(route_line, color="blue", weight=5, opacity=0.8).add_to(m)
    else:
        st.warning("경로 정보를 가져오지 못했습니다.")

    # Streamlit에 지도 표시
    st_folium(m, width=700, height=500)
