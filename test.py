import streamlit as st
import requests

# 카카오 REST API 키
KAKAO_REST_API_KEY = "여기에_본인_KAKAO_REST_API_KEY_입력"
# 카카오 JavaScript API 키
KAKAO_JS_API_KEY = "여기에_본인_KAKAO_JAVASCRIPT_API_KEY_입력"

def get_coordinates(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": address}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        documents = response.json().get("documents")
        if documents:
            x = documents[0]["x"]
            y = documents[0]["y"]
            return float(x), float(y)
    return None, None

# Streamlit UI
st.title("카카오 지도 길찾기 데모")

start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")

if st.button("길찾기 검색"):
    start_x, start_y = get_coordinates(start_address)
    end_x, end_y = get_coordinates(end_address)

    if None in (start_x, start_y, end_x, end_y):
        st.error("주소를 찾을 수 없습니다. 다시 입력해주세요.")
    else:
        st.success("주소 검색 성공! 지도를 표시합니다.")

        # 카카오 지도 HTML 삽입
        map_html = f"""
        <div id="map" style="width:100%;height:500px;"></div>
        <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_API_KEY}&libraries=services"></script>
        <script>
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
        </script>
        """

        st.components.v1.html(map_html, height=600)
