import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ✅ API 키
kakao_api_key = "12ef3a654aaaed8710e1f5a04454d0a2"
tmap_api_key = "MSQEscmmjL6QqEvry9SJ47eodN5WnKD6R9kv5ie4"

# 주소 또는 키워드 → 좌표 변환 함수
def address_to_coord(address, kakao_api_key):
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}

    # 1️⃣ 주소 검색
    url_address = "https://dapi.kakao.com/v2/local/search/address.json"
    response = requests.get(url_address, headers=headers, params={"query": address}).json()
    documents = response.get("documents", [])

    if documents:
        x = float(documents[0]["x"])
        y = float(documents[0]["y"])
        return x, y

    # 2️⃣ 키워드 검색 (범용 검색)
    url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
    response_keyword = requests.get(url_keyword, headers=headers, params={"query": address}).json()
    keyword_docs = response_keyword.get("documents", [])

    if keyword_docs:
        x = float(keyword_docs[0]["x"])
        y = float(keyword_docs[0]["y"])
        st.info(f"⚠️ 주소 검색 실패 → 키워드 검색 결과 사용: {keyword_docs[0]['place_name']}")
        return x, y

    # 3️⃣ 실패
    return None, None

# TMAP 경로 요청 함수 + 요약 정보 반환
def get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key):
    headers = {
        "appKey": tmap_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    if route_type == "대중교통":
        url = "https://apis.openapi.sk.com/transit/routes"
        payload = {
            "startX": str(start_x),
            "startY": str(start_y),
            "endX": str(end_x),
            "endY": str(end_y)
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            st.error(f"대중교통 API 요청 실패: 상태 코드 {response.status_code}")
            st.write(response.text)
            return [], None
        data = response.json()
        routes = data.get("routes", [])
        if not routes:
            st.warning("대중교통 경로를 찾을 수 없습니다.")
            return [], None
        route = routes[0]
        summary = {
            "totalDistance": route.get("totalDistance", 0),
            "totalTime": route.get("totalTime", 0),
            "totalFare": route.get("totalFare", "정보 없음")
        }
        features = []
        for segment in route.get("segments", []):
            geometry = segment.get("geometry")
            if geometry:
                features.append({"geometry": geometry})
        # 응답 데이터도 세션에 저장해 출력 가능하도록 반환
        return features, summary, data

    # 도보, 자동차 경로 처리
    if route_type == "자동차":
        url = "https://apis.openapi.sk.com/tmap/routes"
    else:  # 도보
        url = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&format=json"

    payload = {
        "startX": str(start_x),
        "startY": str(start_y),
        "endX": str(end_x),
        "endY": str(end_y),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
    }

    if route_type == "도보":
        payload["startName"] = "출발지"
        payload["endName"] = "도착지"
    if route_type == "자동차":
        payload["searchOption"] = "0"

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        st.error(f"{route_type} API 요청 실패: 상태 코드 {response.status_code}")
        st.write(response.text)
        return [], None, None
    data = response.json()
    features = data.get("features", [])
    summary = None
    if features:
        properties = features[0].get("properties", {})
        summary = {
            "totalDistance": properties.get("totalDistance", 0),
            "totalTime": properties.get("totalTime", 0),
            "totalFare": properties.get("totalFare", 0),
            "taxiFare": properties.get("taxiFare", 0)
        }
    return features, summary, data

# Streamlit UI
st.title("🚗 경로 검색 웹앱 (카카오맵 + TMAP API)")

st.header("🗺️ 경로 설정")
start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")
route_type = st.selectbox("경로 유형 선택", ["도보", "자동차", "대중교통"])

if st.button("경로 검색"):
    start_x, start_y = address_to_coord(start_address, kakao_api_key)
    end_x, end_y = address_to_coord(end_address, kakao_api_key)

    if None in [start_x, start_y, end_x, end_y]:
        st.error("출발지 또는 도착지 주소를 찾을 수 없습니다.")
    else:
        st.success(f"출발지 좌표: ({start_y}, {start_x})\n도착지 좌표: ({end_y}, {end_x})")
        features, summary, raw_data = get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key)

        if features is None:
            st.error("경로 정보를 가져오지 못했습니다.")
        else:
            # 세션 상태 저장
            st.session_state['map_features'] = features
            st.session_state['start_coord'] = (start_y, start_x)
            st.session_state['end_coord'] = (end_y, end_x)
            st.session_state['route_summary'] = summary
            st.session_state['route_type'] = route_type
            if route_type == "대중교통":
                st.session_state['transit_raw'] = raw_data

# 결과 출력 및 지도 그리기
if 'map_features' in st.session_state:
    features = st.session_state['map_features']
    start_y, start_x = st.session_state['start_coord']
    end_y, end_x = st.session_state['end_coord']
    summary = st.session_state['route_summary']
    route_type = st.session_state.get('route_type', '도보')

    if summary:
        st.subheader("📊 경로 요약 정보")
        st.write(f"**총 거리:** {summary.get('totalDistance', 0) / 1000:.1f} km")
        st.write(f"**총 소요 시간:** {summary.get('totalTime', 0) / 60:.0f} 분")
        st.write(f"**총 요금:** {summary.get('totalFare', '정보 없음')} 원")

    m = folium.Map(location=[(start_y + end_y) / 2, (start_x + end_x) / 2], zoom_start=13)
    folium.Marker([start_y, start_x], tooltip="출발지", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_y, end_x], tooltip="도착지", icon=folium.Icon(color='red')).add_to(m)

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

    st_folium(m, width=700, height=500)

    # 대중교통 API 원본 응답 JSON 출력 (대중교통 선택 시)
    if route_type == "대중교통" and 'transit_raw' in st.session_state:
        st.subheader("🚌 대중교통 API 응답 JSON (원본)")
        st.json(st.session_state['transit_raw'])
