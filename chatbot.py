import streamlit as st
import openai
import pdfplumber
from duckduckgo_search import DDGS

# 웹 검색 함수
def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
        combined = "\n\n".join(f"{r['title']}\n{r['body']}" for r in results)
        return combined if combined else "검색 결과를 찾을 수 없습니다."

# PDF에서 텍스트 추출
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

# TXT 파일에서 텍스트 추출
def extract_text_from_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8")

# OpenAI GPT-4 응답 함수
def get_chat_response(api_key, messages):
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

# Streamlit 앱 시작
st.set_page_config(page_title="GPT 챗봇", layout="wide")
st.title("GPT-4 챗봇")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 웹 검색, PDF 분석, 코드 파일 분석이 가능한 GPT-4 도우미입니다."}
    ]
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# API 키 입력
api_key = st.text_input("OpenAI API 키를 입력하세요", type="password", key="api_key")

if not api_key:
    st.warning("API 키를 입력해야 챗봇을 사용할 수 있습니다.")
    st.stop()

# 파일 업로드
pdf_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])
txt_file = st.file_uploader("TXT 파일 업로드", type=["txt"])

# 질문 입력
user_input = st.text_area("질문을 입력하세요", height=100, key="user_input")

submit = st.button("질문하기")

# 대화 초기화 버튼
if st.button("대화 초기화"):
    st.session_state.messages = [
        {"role": "system", "content": "당신은 웹 검색, PDF 분석, 코드 파일 분석이 가능한 GPT-4 도우미입니다."}
    ]
    st.session_state.user_input = ""
    st.experimental_rerun()

if submit and user_input.strip():
    context = ""

    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        context += "\n\n[PDF 내용]\n" + pdf_text

    if txt_file:
        txt_text = extract_text_from_txt(txt_file)
        context += "\n\n[TXT 내용]\n" + txt_text

    web_result = search_web(user_input)
    context += "\n\n[웹 검색 결과]\n" + web_result

    full_prompt = f"{user_input}\n\n[참고 자료]\n{context}"

    st.session_state.messages.append({"role": "user", "content": full_prompt})

    with st.spinner("응답 생성 중..."):
        assistant_reply = get_chat_response(api_key, st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    st.session_state.user_input = ""

# 대화 기록 출력 (시스템 메시지 제외)
for msg in st.session_state.messages[1:]:
    role = "사용자" if msg["role"] == "user" else "챗봇"
    st.markdown(f"**{role}:** {msg['content']}")
