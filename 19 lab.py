import streamlit as st
import openai
import time
import fitz  # PyMuPDF

# Streamlit 페이지 설정
st.set_page_config(page_title="GPT-4o Mini Web App", layout="centered")

# 세션 상태 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "library_chat_history" not in st.session_state:
    st.session_state.library_chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# 사이드바 API 키 입력
st.session_state.api_key = st.sidebar.text_input(
    "OpenAI API Key 입력", type="password", value=st.session_state.api_key,
)

if st.sidebar.button("API Key 초기화"):
    st.session_state.api_key = ""

def get_client():
    return openai.OpenAI(api_key=st.session_state.api_key)

# PDF 텍스트 추출 함수
def extract_pdf_text(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text()  # 페이지에서 텍스트 추출
    return text

# Chat Completion을 사용한 답변 생성 함수
def get_response_from_pdf(api_key, question, pdf_text):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Here is some information from the document: {pdf_text[:1000]}... Please answer the following question based on this content."},
        {"role": "user", "content": question}
    ]
    
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()

# 페이지 선택
page = st.sidebar.selectbox("페이지 선택", ["Q&A", "Chat", "Chatbot", "ChatPDF"])

def reset_session_state():
    st.session_state.chat_history = []
    st.session_state.library_chat_history = []
    st.session_state.pdf_text = ""

# Q&A 페이지
if page == "Q&A":
    st.title("GPT-4o Mini 질문 응답기")
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    user_input = st.text_area("질문을 입력하세요:", height=100)
    if st.button("질문하기"):
        if user_input.strip() == "":
            st.warning("질문을 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            with st.spinner("응답 생성 중..."):
                answer = get_response_from_pdf(st.session_state.api_key, user_input, st.session_state.pdf_text)
                st.subheader("응답:")
                st.write(answer)

# ChatPDF 페이지
elif page == "ChatPDF":
    st.title("ChatPDF - PDF 기반 챗봇")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (1개만)", type=["pdf"])

    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    if uploaded_file:
        st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("PDF 텍스트 추출 완료!")

        user_input_pdf = st.text_area("PDF에 대해 질문해보세요:", height=100)
        if st.button("질문하기"):
            if user_input_pdf.strip() == "":
                st.warning("질문을 입력해주세요.")
            elif not st.session_state.api_key:
                st.warning("API Key를 입력해 주세요.")
            else:
                with st.spinner("응답 생성 중..."):
                    answer = get_response_from_pdf(st.session_state.api_key, user_input_pdf, st.session_state.pdf_text)
                    st.subheader("응답:")
                    st.write(answer)
    elif not uploaded_file and st.session_state.pdf_text:
        st.warning("PDF를 먼저 업로드 해주세요.")

# Chatbot 페이지
elif page == "Chatbot":
    st.title("국립부경대학교 도서관 챗봇")
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    st.session_state.library_input = st.text_area("도서관에 대해 궁금한 점을 입력하세요:", height=100)
    library_regulations = """
    제20조(휴관일)
    도서관의 휴관일은 다음 각 호와 같다. 다만, 관장은 필요에 따라 이를 조정할 수 있다.
    1. 자료실: 공휴일, 개교기념일
    2. 일반열람실: 설날, 추석

    제22조(대출책수 및 기간)
    1. 전임교원, 겸임교원, 명예교수, 강사: 50책 이내 90일
    2. 직원, 조교, 대학원생: 20책 이내 30일
    3. 학부생: 5책 이내 10일
    """
    if st.button("질문하기"):
        if st.session_state.library_input.strip() == "":
            st.warning("질문을 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            st.session_state.library_chat_history.append({"role": "user", "content": st.session_state.library_input})
            messages = [
                {"role": "system", "content": f"당신은 국립부경대학교 도서관 규정에 대해 안내하는 챗봇입니다. 다음은 도서관 규정입니다:\n{library_regulations}"}
            ] + st.session_state.library_chat_history
            assistant_reply = get_response_from_pdf(st.session_state.api_key, st.session_state.library_input, "")
            st.session_state.library_chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.library_chat_history:
        role = "사용자" if msg["role"] == "user" else "도서관 챗봇"
        st.markdown(f"**{role}:** {msg['content']}")

# 기본적인 챗봇 페이지
elif page == "Chat":
    st.title("GPT-4o Mini 챗봇")
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    user_input_chat = st.text_area("메시지를 입력하세요:", height=100)
    if st.button("질문하기"):
        if user_input_chat.strip() == "":
            st.warning("메시지를 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_input_chat})
            messages = [{"role": "system", "content": "당신은 친절하고 유용한 챗봇입니다."}] + st.session_state.chat_history
            assistant_reply = get_response_from_pdf(st.session_state.api_key, user_input_chat, st.session_state.pdf_text)
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})

    for msg in st.session_state.chat_history:
        role = "사용자" if msg["role"] == "user" else "GPT"
        st.markdown(f"**{role}:** {msg['content']}")
