import streamlit as st
import requests

def get_coordinates(address, api_key):
    headers = {"Authorization": f"KakaoAK {api_key}"}

    # 1. 주소 검색 시도
    url_addr = "https://dapi.kakao.com/v2/local/search/address.json"
    params_addr = {"query": address.strip()}
    res_addr = requests.get(url_addr, headers=headers, params=params_addr)
    if res_addr.status_code == 200:
        json_addr = res_addr.json()
        if json_addr.get("documents"):
            x = json_addr["documents"][0]["x"]
            y = json_addr["documents"][0]["y"]
            return float(x), float(y)

    # 2. 키워드 검색 시도
    url_key = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params_key = {"query": address.strip(), "size": 1}
    res_key = requests.get(url_key, headers=headers, params=params_key)
    if res_key.status_code == 200:
        json_key = res_key.json()
        if json_key.get("documents"):
            x = json_key["documents"][0]["x"]
            y = json_key["documents"][0]["y"]
            return float(x), float(y)

    return None, None

st.title("카카오 지도 길찾기 웹 링크 생성기 (주소+키워드 검색 포함)")

rest_api_key = st.text_input("Kakao REST API Key", type="password")

start_addr = st.text_input("출발지 주소", "서울역")
end_addr = st.text_input("도착지 주소", "강남역")

if st.button("길찾기 링크 생성"):
    if not rest_api_key:
        st.error("REST API 키를 입력하세요.")
    else:
        start_x, start_y = get_coordinates(start_addr, rest_api_key)
        end_x, end_y = get_coordinates(end_addr, rest_api_key)

        if None in (start_x, start_y, end_x, end_y):
            st.error("주소를 찾을 수 없습니다. 다시 입력해주세요.")
        else:
            kakao_map_url = (
    f"https://map.kakao.com/?fromCoord={start_x},{start_y}"
    f"&toCoord={end_x},{end_y}"
    f"&from={start_addr}&to={end_addr}"
)
            st.markdown(f"[카카오 지도 길찾기 바로가기]({kakao_map_url})", unsafe_allow_html=True)
