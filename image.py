import streamlit as st
from PIL import Image
import pytesseract
import openai

st.title("이미지 텍스트 추출 + GPT-4o 질문 챗봇")

# API 키 입력
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.text_input("OpenAI API 키를 입력하세요", type="password")
if api_key:
    st.session_state.api_key = api_key

if not st.session_state.api_key:
    st.warning("API 키를 입력해야 사용 가능합니다.")
    st.stop()

openai.api_key = st.session_state.api_key

# 이미지 업로드
uploaded_file = st.file_uploader("이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

# 질문 입력
user_question = st.text_input("질문을 입력하세요")

def extract_text_from_image(image: Image.Image) -> str:
    # pytesseract로 이미지에서 텍스트 추출
    text = pytesseract.image_to_string(image, lang='kor+eng')  # 한글+영어 추출 가능
    return text.strip()

def ask_gpt(question: str, extracted_text: str) -> str:
    prompt = f"""아래는 이미지에서 추출한 텍스트입니다:
---
{extracted_text}

이 텍스트를 참고하여 사용자의 질문에 답변해 주세요:
{question}
"""
    messages = [
        {"role": "system", "content": "당신은 이미지에서 추출한 텍스트를 참고해 질문에 답변하는 유능한 비서입니다."},
        {"role": "user", "content": prompt}
    ]
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()

if uploaded_file and user_question:
    image = Image.open(uploaded_file)
    with st.spinner("이미지에서 텍스트를 추출하는 중입니다..."):
        extracted_text = extract_text_from_image(image)
    st.markdown("### 이미지에서 추출한 텍스트:")
    st.write(extracted_text or "텍스트가 감지되지 않았습니다.")

    with st.spinner("GPT-4o 모델이 답변을 생성 중입니다..."):
        answer = ask_gpt(user_question, extracted_text)
    st.markdown("### GPT-4o 답변:")
    st.write(answer)
elif user_question:
    st.info("이미지를 먼저 업로드해주세요.")
