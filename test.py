import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ✅ 사용자에게 API 키 입력받기
kakao_api_key = st.text_input("Kakao REST API 키 입력", type="password")
tmap_api_key = st.text_input("Tmap API 키 입력", type="password")

# 주소 또는 키워드 → 좌표 변환 함수
def address_to_coord(address, kakao_api_key):
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
    url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": address}

    response = requests.get(url_keyword, headers=headers, params=params).json()
    documents = response.get("documents", [])

    if documents:
        x = float(documents[0]["x"])
        y = float(documents[0]["y"])
        st.info(f"📍 키워드 검색 결과: {documents[0]['place_name']}")
        return x, y

    st.error(f"❌ '{address}'에 대한 장소를 찾을 수 없습니다.")
    return None, None

# TMAP 경로 요청 함수
def get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key):
    if route_type == "자동차":
        url = "https://apis.openapi.sk.com/tmap/routes"
    else:  # 도보
        url = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&format=json"

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
        "resCoordType": "WGS84GEO"
    }

    if route_type == "도보":
        payload["startName"] = "출발지"
        payload["endName"] = "도착지"
    else:
        payload["searchOption"] = "0"

    response = requests.post(url, headers=headers, json=payload).json()
    features = response.get("features", [])

    summary = None
    if features:
        props = features[0].get("properties", {})
        summary = {
            "totalDistance": props.get("totalDistance", 0),
            "totalTime": props.get("totalTime", 0),
            "totalFare": props.get("totalFare", 0),
            "taxiFare": props.get("taxiFare", 0)
        }

    return features, summary

# Streamlit UI 구성
st.title("🚗 여행지 경로 검색")

# 출발지/도착지 입력
start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")
route_type = st.selectbox("경로 유형 선택", ["도보", "자동차"])

# 경로 검색 버튼
if st.button("경로 검색"):
    if not kakao_api_key or not tmap_api_key:
        st.error("API 키를 모두 입력해주세요.")
    else:
        start_x, start_y = address_to_coord(start_address, kakao_api_key)
        end_x, end_y = address_to_coord(end_address, kakao_api_key)

        if None in [start_x, start_y, end_x, end_y]:
            st.error("출발지 또는 도착지 주소를 찾을 수 없습니다.")
        else:
            features, summary = get_tmap_route(start_x, start_y, end_x, end_y, route_type, tmap_api_key)

            st.session_state['map_features'] = features
            st.session_state['start_coord'] = (start_y, start_x)
            st.session_state['end_coord'] = (end_y, end_x)
            st.session_state['route_summary'] = summary

# 지도 출력
if 'map_features' in st.session_state:
    features = st.session_state['map_features']
    start_y, start_x = st.session_state['start_coord']
    end_y, end_x = st.session_state['end_coord']
    summary = st.session_state['route_summary']

    if summary:
        st.subheader("📊 경로 요약 정보")
        st.write(f"**총 거리:** {summary['totalDistance'] / 1000:.1f} km")
        st.write(f"**총 소요 시간:** {summary['totalTime'] / 60:.0f} 분")
        st.write(f"**총 요금:** {summary['totalFare']} 원")
        st.write(f"**예상 택시 요금:** {summary['taxiFare']} 원")

    m = folium.Map(location=[(start_y + end_y) / 2, (start_x + end_x) / 2], zoom_start=13)
    folium.Marker([start_y, start_x], tooltip="출발지", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_y, end_x], tooltip="도착지", icon=folium.Icon(color='red')).add_to(m)

    route_line = []
    for feature in features:
        geometry = feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            coords = geometry.get("coordinates", [])
            for lon, lat in coords:
                route_line.append((lat, lon))

    if route_line:
        folium.PolyLine(route_line, color="blue", weight=5).add_to(m)
    else:
        st.warning("경로 정보를 가져오지 못했습니다.")

    st_folium(m, width=700, height=500)
