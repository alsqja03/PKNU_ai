import streamlit as st
import googlemaps
import folium
from streamlit_folium import st_folium
import polyline

# Google Directions API 호출 함수
def get_directions(gmaps, origin, destination, mode):
    directions_result = gmaps.directions(origin, destination, mode=mode)
    return directions_result

def main():
    st.title("Google Directions API 연동 예제")

    # API 키 입력받기
    api_key = st.text_input("Google API Key 입력", type="password")
    if not api_key:
        st.warning("API 키를 입력해주세요")
        return

    gmaps = googlemaps.Client(key=api_key)

    # 출발지, 도착지 입력
    origin = st.text_input("출발지 입력")
    destination = st.text_input("도착지 입력")

    mode = st.selectbox("이동 수단 선택", ["driving", "transit", "walking"])

    if st.button("길찾기"):
        if not origin or not destination:
            st.error("출발지와 도착지를 모두 입력해주세요")
            return

        try:
            directions = get_directions(gmaps, origin, destination, mode)

            if not directions:
                st.error("경로를 찾을 수 없습니다.")
                return

            leg = directions[0]['legs'][0]

            # 지도 중심 위치 (출발지)
            map_center = [leg['start_location']['lat'], leg['start_location']['lng']]
            m = folium.Map(location=map_center, zoom_start=13)

            # 출발지 마커
            folium.Marker(
                [leg['start_location']['lat'], leg['start_location']['lng']],
                popup=f"출발지: {leg['start_address']}",
                icon=folium.Icon(color='green')
            ).add_to(m)

            # 도착지 마커
            folium.Marker(
                [leg['end_location']['lat'], leg['end_location']['lng']],
                popup=f"도착지: {leg['end_address']}",
                icon=folium.Icon(color='red')
            ).add_to(m)

            # 경로 polyline 만들기
            points = []
            for step in leg['steps']:
                points += polyline.decode(step['polyline']['points'])

            folium.PolyLine(points, color='blue', weight=5, opacity=0.7).add_to(m)

            st_folium(m, width=700, height=500)

        except Exception as e:
            st.error(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
