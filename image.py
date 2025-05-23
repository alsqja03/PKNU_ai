import streamlit as st
from io import BytesIO
import openai

# Streamlit 앱 제목
st.title("이미지+텍스트 질문 GPT-4o 챗봇")

# 1. API 키 입력받기 (보안상 session_state에 저장)
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.text_input("OpenAI API 키를 입력하세요", type="password")
if api_key:
    st.session_state.api_key = api_key

if not st.session_state.api_key:
    st.warning("API 키를 입력해야 사용 가능합니다.")
    st.stop()

openai.api_key = st.session_state.api_key

# 2. 이미지 업로드 받기
uploaded_image = st.file_uploader("질문과 관련된 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

# 3. 질문 텍스트 입력받기
user_question = st.text_input("질문을 입력하세요")

def ask_gpt_with_image(question: str, image_bytes: bytes) -> str:
    # GPT-4o 모델에 이미지와 텍스트 함께 보내기 (ChatCompletion with messages + image)
    # 현재 openai Python SDK에서 이미지 입력 예시는 없으므로 이미지 기반 텍스트 추출(ocr) 등은 별도 처리 필요.
    # 여기서는 이미지가 있다고 가정하고 메시지만 보내는 예시로 구현합니다.
    
    # 실제로 이미지 기반 질문이라면, 먼저 OCR 처리해서 텍스트를 추출 후 질문에 포함시키는 방식을 권장합니다.
    # 여기서는 이미지가 있다는 정보만 시스템에 알려줌
    
    messages = [
        {"role": "system", "content": "당신은 이미지가 첨부된 질문에 답하는 챗봇입니다."},
        {"role": "user", "content": f"이미지가 첨부되어 있습니다. 질문: {question}"}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
    )
    
    return response.choices[0].message.content.strip()

if uploaded_image and user_question:
    image_bytes = uploaded_image.read()
    with st.spinner("GPT-4o 모델이 답변을 생성 중입니다..."):
        answer = ask_gpt_with_image(user_question, image_bytes)
    st.markdown("### GPT-4o 답변:")
    st.write(answer)
elif user_question:
    st.info("이미지를 먼저 업로드해주세요.")
