import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

# 카카오 로컬 API 주소 및 키워드 검색 API
ADDR_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

TRANSPORT_TYPE = {
    "자동차": "CAR",
    "대중교통": "PUBLICTRANSIT",
    "도보": "WALK"
}

st.title("KakaoMap 경로 검색")

api_key = st.text_input("카카오 REST API 키를 입력하세요", type="password")

start = st.text_input("출발지 주소 또는 장소명")
end = st.text_input("도착지 주소 또는 장소명")

mode = st.radio("이동수단 선택", ("자동차", "대중교통", "도보"))

def get_coords(query, api_key):
    """주소 검색 실패 시 키워드 검색까지 시도해 좌표 리턴"""
    headers = {"Authorization": f"KakaoAK {api_key}"}
    
    # 1. 주소 검색 시도
    params_addr = {"query": query}
    res = requests.get(ADDR_SEARCH_URL, headers=headers, params=params_addr)
    if res.status_code == 200:
        documents = res.json().get("documents")
        if documents:
            doc = documents[0]
            x = float(doc["x"])
            y = float(doc["y"])
            st.write(f"주소검색 성공: '{query}' → 위도:{y}, 경도:{x}")
            return y, x
        else:
            st.write(f"주소검색 결과 없음: '{query}'")
    else:
        st.write(f"주소검색 API 오류: {res.status_code}")

    # 2. 키워드 검색 시도
    params_keyword = {"query": query}
    res = requests.get(KEYWORD_SEARCH_URL, headers=headers, params=params_keyword)
    if res.status_code == 200:
        documents = res.json().get("documents")
        if documents:
            doc = documents[0]
            x = float(doc["x"])
            y = float(doc["y"])
            st.write(f"키워드검색 성공: '{query}' → 위도:{y}, 경도:{x}")
            return y, x
        else:
            st.write(f"키워드검색 결과 없음: '{query}'")
    else:
        st.write(f"키워드검색 API 오류: {res.status_code}")

    return None

def get_route(start_coords, end_coords, mode, api_key):
    """
    실제 카카오 내비 API는 별도 권한이 필요해 여기선 단순 직선 폴리라인만 반환합니다.
    """
    return [start_coords, end_coords]

if api_key and start and end:
    start_coords = get_coords(start, api_key)
    end_coords = get_coords(end, api_key)

    if not start_coords or not end_coords:
        st.error("출발지 또는 도착지 좌표를 찾을 수 없습니다. 주소나 장소명을 다시 확인하세요.")
    else:
        st.success(f"출발지 좌표: {start_coords}, 도착지 좌표: {end_coords}")

        route_coords = get_route(start_coords, end_coords, TRANSPORT_TYPE[mode], api_key)

        # 지도 중앙 계산
        center_lat = (start_coords[0] + end_coords[0]) / 2
        center_lon = (start_coords[1] + end_coords[1]) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # 출발지, 도착지 마커 추가
        folium.Marker(start_coords, tooltip="출발지", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(end_coords, tooltip="도착지", icon=folium.Icon(color='red')).add_to(m)

        # 경로(직선) 폴리라인 추가
        folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

        st_folium(m, width=700, height=500)
else:
    st.info("카카오 REST API 키, 출발지, 도착지를 모두 입력해주세요.")
