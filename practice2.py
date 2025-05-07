import streamlit as st
import openai

# 페이지 설정
st.set_page_config(page_title="GPT-4.1 Mini Web App", layout="centered")

# 세션 상태 설정
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "library_chat_history" not in st.session_state:
    st.session_state.library_chat_history = []
if "pdf_file_id" not in st.session_state:
    st.session_state.pdf_file_id = None
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# 페이지 선택
page = st.sidebar.selectbox("페이지 선택", ["Q&A", "Chat", "Chatbot", "ChatPDF"])

# OpenAI API Key 입력
st.session_state.api_key = st.sidebar.text_input(
    "OpenAI API Key 입력",
    type="password",
    value=st.session_state.api_key,
)

# OpenAI API 호출 함수
def get_response(api_key, messages):
    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-4.1-mini",  # GPT-4 모델을 사용합니다
            messages=messages  # 메시지 목록을 전달
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"API 요청 오류: {e}")
        return None

# 세션 초기화 함수
def reset_session_state(clear_api_key=False):
    st.session_state.chat_history = []
    st.session_state.library_chat_history = []
    st.session_state.pdf_file_id = None
    st.session_state.assistant_id = None
    st.session_state.thread_id = None
    if clear_api_key:
        st.session_state.api_key = ""

# 페이지별 로직
if page == "Q&A":
    st.title("GPT-4.1 Mini 질문 응답기")
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state(clear_api_key=False)  # 메시지만 초기화
    
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
                if answer:
                    st.subheader("응답:")
                    st.write(answer)

elif page == "Chat":
    st.title("GPT-4.1 Mini 챗봇")
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state(clear_api_key=False)  # 메시지만 초기화
    
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
            if assistant_reply:
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.chat_history:
        role = "사용자" if msg["role"] == "user" else "GPT"
        st.markdown(f"**{role}:** {msg['content']}")

elif page == "Chatbot":
    st.title("국립부경대학교 도서관 챗봇")
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state(clear_api_key=False)  # 메시지만 초기화
    
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
            if assistant_reply:
                st.session_state.library_chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.library_chat_history:
        role = "사용자" if msg["role"] == "user" else "도서관 챗봇"
        st.markdown(f"**{role}:** {msg['content']}")

elif page == "ChatPDF":
    st.title("ChatPDF - PDF 기반 챗봇")
    
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (1개만)", type=["pdf"])
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state(clear_api_key=False)  # 메시지만 초기화
    
    if uploaded_file and st.session_state.api_key:
        if not st.session_state.pdf_file_id:
            file_id = upload_pdf(uploaded_file)
            st.session_state.pdf_file_id = file_id
            assistant_id = create_assistant(file_id)
            st.session_state.assistant_id = assistant_id
            st.success("PDF 업로드 및 어시스턴트 준비 완료!")
    if st.session_state.pdf_file_id:
        user_question = st.text_area("PDF에 대해 질문해보세요:", height=100)
        if st.button("질문하기"):
            if user_question.strip() == "":
                st.warning("질문을 입력해주세요.")
            else:
                try:
                    answer = chat_with_pdf(
                        st.session_state.assistant_id,
                        st.session_state.pdf_file_id,
                        user_question
                    )
                    st.subheader("응답:")
                    st.write(answer)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    elif uploaded_file and not st.session_state.api_key:
        st.warning("API Key를 입력해 주세요.")
