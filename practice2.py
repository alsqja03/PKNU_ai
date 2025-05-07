import streamlit as st
import openai
import PyPDF2
from io import BytesIO

# 세션 상태 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "library_chat_history" not in st.session_state:
    st.session_state.library_chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

st.set_page_config(page_title="GPT-4.1 Mini Web App", layout="centered")

# OpenAI API 설정
openai.api_key = st.session_state.api_key

def extract_text_from_pdf(uploaded_file):
    try:
        # PDF 텍스트 추출
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"PDF 파일을 읽는 중 오류 발생: {e}")
        return ""

def get_response_from_pdf(api_key: str, pdf_text: str, user_message: str) -> str:
    openai.api_key = api_key
    prompt = f"다음 PDF 내용을 바탕으로 질문에 대답하세요:\n{pdf_text}\n질문: {user_message}"
    response = openai.Completion.create(
        model="gpt-4.1-mini",  # GPT-4.1 Mini 모델 사용
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def get_response(api_key: str, messages: list) -> str:
    openai.api_key = api_key
    response = openai.Completion.create(
        model="gpt-4.1-mini",  # GPT-4.1 Mini 모델 사용
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def reset_session_state(clear_api_key=False):
    st.session_state.chat_history = []
    st.session_state.library_chat_history = []
    st.session_state.pdf_text = ""
    if clear_api_key:
        st.session_state.api_key = ""

# 페이지 로직
page = st.sidebar.selectbox("페이지 선택", ["Q&A", "Chat", "Chatbot", "ChatPDF"])

st.session_state.api_key = st.sidebar.text_input(
    "OpenAI API Key 입력",
    type="password",
    value=st.session_state.api_key,
)

# Q&A 페이지
if page == "Q&A":
    st.title("GPT-4.1 Mini 질문 응답기")
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    question = st.text_area("질문을 입력하세요:", height=100)
    if st.button("질문하기"):
        if question.strip() == "":
            st.warning("질문을 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            with st.spinner("응답 생성 중..."):
                messages = [
                    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
                    {"role": "user", "content": question}
                ]
                answer = get_response(st.session_state.api_key, messages)
                st.subheader("응답:")
                st.write(answer)

# Chat 페이지
elif page == "Chat":
    st.title("GPT-4.1 Mini 챗봇")
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    user_input = st.text_area("메시지를 입력하세요:", height=100)
    if st.button("질문하기"):
        if user_input.strip() == "":
            st.warning("메시지를 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            messages = [{"role": "system", "content": "당신은 친절하고 유용한 챗봇입니다."}] + st.session_state.chat_history
            assistant_reply = get_response(st.session_state.api_key, messages)
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.chat_history:
        role = "사용자" if msg["role"] == "user" else "GPT"
        st.markdown(f"**{role}:** {msg['content']}")

# Chatbot 페이지
elif page == "Chatbot":
    st.title("국립부경대학교 도서관 챗봇")
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    user_input = st.text_area("도서관에 대해 궁금한 점을 입력하세요:", height=100)
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
        if user_input.strip() == "":
            st.warning("질문을 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            st.session_state.library_chat_history.append({"role": "user", "content": user_input})
            messages = [
                {"role": "system", "content": f"당신은 국립부경대학교 도서관 규정에 대해 안내하는 챗봇입니다. 다음은 도서관 규정입니다:\n{library_regulations}"}
            ] + st.session_state.library_chat_history
            assistant_reply = get_response(st.session_state.api_key, messages)
            st.session_state.library_chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.library_chat_history:
        role = "사용자" if msg["role"] == "user" else "도서관 챗봇"
        st.markdown(f"**{role}:** {msg['content']}")

# ChatPDF 페이지
elif page == "ChatPDF":
    st.title("ChatPDF - PDF 기반 챗봇")
    
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (1개만)", type=["pdf"])
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    if uploaded_file and st.session_state.api_key:
        # PDF 파일에서 텍스트 추출
        pdf_text = extract_text_from_pdf(uploaded_file)
        if pdf_text:
            st.session_state.pdf_text = pdf_text
            st.success("PDF 파일에서 텍스트를 추출했습니다!")
        
        # PDF 업로드 후 사용자가 질문 입력
        user_question = st.text_area("PDF에 대해 질문해보세요:", height=100)
        if st.button("질문하기"):
            if user_question.strip() == "":
                st.warning("질문을 입력해주세요.")
            else:
                try:
                    answer = get_response_from_pdf(
                        st.session_state.api_key,
                        st.session_state.pdf_text,
                        user_question
                    )
                    st.subheader("응답:")
                    st.write(answer)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    elif uploaded_file and not st.session_state.api_key:
        st.warning("API Key를 입력해 주세요.")
