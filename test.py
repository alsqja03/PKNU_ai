import streamlit as st
import requests

# 상태 저장용 변수
if "current_rest_api_key" not in st.session_state:
    st.session_state.current_rest_api_key = ""
if "current_js_api_key" not in st.session_state:
    st.session_state.current_js_api_key = ""

# 사용자에게 API 키 입력 받기
with st.expander("🔑 카카오 API 키 입력", expanded=True):
    st.session_state.current_rest_api_key = st.text_input(
        "Kakao REST API Key", st.session_state.current_rest_api_key
    )
    st.session_state.current_js_api_key = st.text_input(
        "Kakao JavaScript API Key", st.session_state.current_js_api_key
    )

# 현재 API 키 가져오기
current_rest_api_key = st.session_state.current_rest_api_key
current_js_api_key = st.session_state.current_js_api_key

# 좌표 가져오는 함수 (주소 → 키워드 fallback)
def get_coordinates(address):
    # 1️⃣ 주소 검색 시도
    url_address = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {current_rest_api_key}"}
    params = {"query": address.strip()}

    response_address = requests.get(url_address, headers=headers, params=params)

    st.write(f"📍 (주소 검색) 검색 주소: {address}")
    st.write(f"🔗 요청 URL: {response_address.url}")
    st.write(f"✅ 응답 상태 코드: {response_address.status_code}")

    try:
        response_json_address = response_address.json()
        st.json(response_json_address)
    except Exception as e:
        st.error(f"응답 JSON 파싱 오류 (주소): {e}")
        return None, None

    if response_address.status_code == 200:
        documents = response_json_address.get("documents")
        if documents:
            x = documents[0]["x"]
            y = documents[0]["y"]
            st.info("✅ 주소 검색 성공")
            return float(x), float(y)

    # 2️⃣ 키워드 검색 fallback 시도
    st.warning("⚠️ 주소 검색 결과 없음 → 키워드 검색 시도")

    url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params_keyword = {"query": address.strip(), "size": 1}

    response_keyword = requests.get(url_keyword, headers=headers, params=params_keyword)

    st.write(f"📍 (키워드 검색) 검색 주소: {address}")
    st.write(f"🔗 요청 URL: {response_keyword.url}")
    st.write(f"✅ 응답 상태 코드: {response_keyword.status_code}")

    try:
        response_json_keyword = response_keyword.json()
        st.json(response_json_keyword)
    except Exception as e:
        st.error(f"응답 JSON 파싱 오류 (키워드): {e}")
        return None, None

    if response_keyword.status_code == 200:
        documents = response_json_keyword.get("documents")
        if documents:
            x = documents[0]["x"]
            y = documents[0]["y"]
            st.info("✅ 키워드 검색 성공")
            return float(x), float(y)

    # 둘 다 실패
    return None, None

# Streamlit UI
st.title("🗺️ 카카오 지도 길찾기 데모 (주소 + 키워드 자동 fallback)")

start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")

if st.button("길찾기 검색"):
    # API 키 입력 체크
    if not current_rest_api_key or not current_js_api_key:
        st.error("❌ API 키를 입력하세요.")
    else:
        start_x, start_y = get_coordinates(start_address)
        end_x, end_y = get_coordinates(end_address)

        if None in (start_x, start_y, end_x, end_y):
            st.error("❌ 주소를 찾을 수 없습니다. 다시 입력해주세요.")
        else:
            st.success("✅ 주소 검색 성공! 지도를 표시합니다.")

            # Kakao 지도 HTML
            map_html = f"""
            <div id="map" style="width:100%;height:500px;"></div>
            <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={current_js_api_key}&autoload=false&libraries=services"></script>
            <script>
                kakao.maps.load(function() {{
                    var mapContainer = document.getElementById('map');
                    var mapOption = {{
                        center: new kakao.maps.LatLng({start_y}, {start_x}),
                        level: 5
                    }};
                    var map = new kakao.maps.Map(mapContainer, mapOption);

                    // 출발지 마커
                    var startMarker = new kakao.maps.Marker({{
                        position: new kakao.maps.LatLng({start_y}, {start_x}),
                        map: map,
                        title: '출발지'
                    }});

                    // 도착지 마커
                    var endMarker = new kakao.maps.Marker({{
                        position: new kakao.maps.LatLng({end_y}, {end_x}),
                        map: map,
                        title: '도착지'
                    }});

                    // 선 그리기
                    var linePath = [
                        new kakao.maps.LatLng({start_y}, {start_x}),
                        new kakao.maps.LatLng({end_y}, {end_x})
                    ];

                    var polyline = new kakao.maps.Polyline({{
                        path: linePath,
                        strokeWeight: 5,
                        strokeColor: '#FF0000',
                        strokeOpacity: 0.7,
                        strokeStyle: 'solid'
                    }});

                    polyline.setMap(map);

                    // 지도 영역 재설정 (출발지와 도착지를 모두 포함하도록)
                    var bounds = new kakao.maps.LatLngBounds();
                    bounds.extend(new kakao.maps.LatLng({start_y}, {start_x}));
                    bounds.extend(new kakao.maps.LatLng({end_y}, {end_x}));
                    map.setBounds(bounds);
                }});
            </script>
            """

            st.components.v1.html(map_html, height=600)
