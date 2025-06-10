import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

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

# TMAP 경로 요청 함수
def get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key):
    url = "https://apis.openapi.sk.com/tmap/routes/pedestrian"  # 기본 도보
    if route_type == "자동차":
        url = "https://apis.openapi.sk.com/tmap/routes"
    elif route_type == "대중교통":
        st.warning("TMAP API에서 대중교통은 Web API 미지원 (모바일 SDK 전용). 도보/자동차만 지원됩니다.")
        url = "https://apis.openapi.sk.com/tmap/routes"

    headers = {
        "appKey": tmap_api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "startX": str(start_x),
        "startY": str(start_y),
        "endX": str(end_x),
        "endY": str(end_y),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
    }

    if route_type == "자동차":
        payload.update({
            "searchOption": "0"
        })

    response = requests.post(url, headers=headers, json=payload).json()
    features = response.get("features", [])
    return features

# Streamlit UI 구성
st.title("🚗 경로 검색 웹앱 (카카오맵 + TMAP API)")

# 사용자에게 API 키 입력 받기 (sidebar)
st.sidebar.header("🔑 API Key 입력")
kakao_api_key = st.sidebar.text_input("Kakao REST API Key", type="password")
tmap_api_key = st.sidebar.text_input("TMAP API Key", type="password")

# 출발지/도착지 입력
st.header("🗺️ 경로 설정")
start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")
route_type = st.selectbox("경로 유형 선택", ["도보", "자동차", "대중교통"])

# 경로 검색 버튼
if st.button("경로 검색"):
    if not kakao_api_key or not tmap_api_key:
        st.error("⚠️ Kakao API Key 및 TMAP API Key를 모두 입력하세요.")
    else:
        start_x, start_y = address_to_coord(start_address, kakao_api_key)
        end_x, end_y = address_to_coord(end_address, kakao_api_key)

        if None in [start_x, start_y, end_x, end_y]:
            st.error("출발지 또는 도착지 주소를 찾을 수 없습니다.")
        else:
            st.success(f"출발지 좌표: ({start_y}, {start_x})\n도착지 좌표: ({end_y}, {end_x})")
            features = get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key)

            # 지도 데이터 session state에 저장
            st.session_state['map_features'] = features
            st.session_state['start_coord'] = (start_y, start_x)
            st.session_state['end_coord'] = (end_y, end_x)

# 지도 렌더링
if 'map_features' in st.session_state:
    features = st.session_state['map_features']
    start_y, start_x = st.session_state['start_coord']
    end_y, end_x = st.session_state['end_coord']

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
