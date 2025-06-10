import streamlit as st
import requests

# 상태 저장용 변수
if "current_rest_api_key" not in st.session_state:
    st.session_state.current_rest_api_key = ""
if "current_js_api_key" not in st.session_state:
    st.session_state.current_js_api_key = ""

with st.expander("🔑 카카오 API 키 입력", expanded=True):
    st.session_state.current_rest_api_key = st.text_input("Kakao REST API Key", st.session_state.current_rest_api_key)
    st.session_state.current_js_api_key = st.text_input("Kakao JavaScript API Key", st.session_state.current_js_api_key)

current_rest_api_key = st.session_state.current_rest_api_key
current_js_api_key = st.session_state.current_js_api_key

def get_coordinates(address):
    headers = {"Authorization": f"KakaoAK {current_rest_api_key}"}

    # 1. 주소 검색 시도
    url_addr = "https://dapi.kakao.com/v2/local/search/address.json"
    params_addr = {"query": address.strip()}
    res_addr = requests.get(url_addr, headers=headers, params=params_addr)
    st.write(f"📍 (주소 검색) 검색 주소: {address}")
    st.write(f"🔗 요청 URL: {res_addr.url}")
    st.write(f"✅ 응답 상태 코드: {res_addr.status_code}")
    try:
        json_addr = res_addr.json()
        st.json(json_addr)
    except Exception as e:
        st.error(f"주소 검색 응답 JSON 파싱 오류: {e}")
        return None, None

    if res_addr.status_code == 200 and json_addr.get("documents"):
        x = json_addr["documents"][0]["x"]
        y = json_addr["documents"][0]["y"]
        st.info("✅ 주소 검색 성공")
        return float(x), float(y)

    st.warning("⚠️ 주소 검색 결과 없음 → 키워드 검색 시도")

    # 2. 키워드 검색 시도
    url_keyword = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params_keyword = {"query": address.strip(), "size": 1}
    res_key = requests.get(url_keyword, headers=headers, params=params_keyword)
    st.write(f"📍 (키워드 검색) 검색 주소: {address}")
    st.write(f"🔗 요청 URL: {res_key.url}")
    st.write(f"✅ 응답 상태 코드: {res_key.status_code}")
    try:
        json_key = res_key.json()
        st.json(json_key)
    except Exception as e:
        st.error(f"키워드 검색 응답 JSON 파싱 오류: {e}")
        return None, None

    if res_key.status_code == 200 and json_key.get("documents"):
        x = json_key["documents"][0]["x"]
        y = json_key["documents"][0]["y"]
        st.info("✅ 키워드 검색 성공")
        return float(x), float(y)

    return None, None

st.title("🗺️ 카카오 지도 길찾기 (iframe 외부 map.html 활용)")

start_address = st.text_input("출발지 입력", "서울역")
end_address = st.text_input("도착지 입력", "강남역")

if st.button("길찾기 검색"):
    if not current_rest_api_key or not current_js_api_key:
        st.error("❌ API 키를 입력하세요.")
    else:
        start_x, start_y = get_coordinates(start_address)
        end_x, end_y = get_coordinates(end_address)

        if None in (start_x, start_y, end_x, end_y):
            st.error("❌ 주소를 찾을 수 없습니다. 다시 입력해주세요.")
        else:
            st.success("✅ 주소 검색 성공! 외부 map.html에서 지도 표시합니다.")

            # 쿼리 스트링으로 좌표 넘기기 (선택사항)
            iframe_url = (
                f"http://pknumap.kro.kr"
                f"?start_x={start_x}&start_y={start_y}&end_x={end_x}&end_y={end_y}"
            )
            st.components.v1.iframe(iframe_url, height=600)
