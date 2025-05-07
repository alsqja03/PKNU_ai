import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="GPT-4o Mini Web App", layout="centered")

# 초기 세션 상태 설정
defaults = {
    "api_key": "",
    "chat_history": [],
    "library_chat_history": [],
    "pdf_file_id": None,
    "assistant_id": None,
    "thread_id": None,
    "clear_flag": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 페이지 선택
page = st.sidebar.selectbox("페이지 선택", ["Q&A", "Chat", "Chatbot", "ChatPDF"])

# API 키 입력
st.session_state.api_key = st.sidebar.text_input("OpenAI API Key 입력", type="password", value=st.session_state.api_key)

# 클라이언트 생성
def get_client():
    return OpenAI(api_key=st.session_state.api_key)

# GPT 응답 함수
def get_response(api_key: str, messages: list) -> str:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# PDF 업로드 처리
def upload_pdf(file):
    client = get_client()
    uploaded = client.files.create(file=(file.name, file), purpose="assistants")
    return uploaded.id

# 어시스턴트 생성
def create_assistant(file_id):
    client = get_client()
    assistant = client.beta.assistants.create(
        name="PDF Chat Assistant",
        instructions="사용자가 업로드한 PDF 내용을 기반으로 친절하게 답변하세요.",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
        file_ids=[file_id],
    )
    return assistant.id

# PDF 챗 응답
def chat_with_pdf(assistant_id, file_id, user_message):
    client = get_client()
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_message,
    )
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
    )
    with st.spinner("응답 생성 중..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id,
            )
            if run_status.status == "completed":
                break
        messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        return messages.data[0].content[0].text.value

# 세션 리셋
def reset_session_state():
    for key in ["chat_history", "library_chat_history", "pdf_file_id", "assistant_id", "thread_id", "clear_flag"]:
        st.session_state[key] = defaults[key]

# API 키 초기화
def clear_api_key():
    st.session_state.api_key = ""

# Q&A 페이지
if page == "Q&A":
    st.title("GPT-4o 질문 응답기")
    question = st.text_area("질문을 입력하세요:", key="qa_input", height=100)

    col1, col2 = st.columns([1, 1])
    with col1:
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
    with col2:
        if st.button("Clear"):
            reset_session_state()
            st.session_state.qa_input = ""

# Chat 페이지
elif page == "Chat":
    st.title("GPT-4o 챗봇")
    user_input = st.text_area("메시지를 입력하세요:", key="chat_input", height=100)

    col1, col2 = st.columns([1, 1])
    with col1:
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
    with col2:
        if st.button("Clear"):
            reset_session_state()
            st.session_state.chat_input = ""

    for msg in st.session_state.chat_history:
        role = "사용자" if msg["role"] == "user" else "GPT"
        st.markdown(f"**{role}:** {msg['content']}")

# Chatbot (도서관 챗봇)
elif page == "Chatbot":
    st.title("국립부경대학교 도서관 챗봇")
    user_input = st.text_area("도서관에 대해 궁금한 점을 입력하세요:", key="lib_input", height=100)

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

    col1, col2 = st.columns([1, 1])
    with col1:
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
    with col2:
        if st.button("Clear"):
            reset_session_state()
            st.session_state.lib_input = ""

    for msg in st.session_state.library_chat_history:
        role = "사용자" if msg["role"] == "user" else "도서관 챗봇"
        st.markdown(f"**{role}:** {msg['content']}")

# ChatPDF 페이지
elif page == "ChatPDF":
    st.title("ChatPDF - PDF 기반 챗봇")
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (1개만)", type=["pdf"])
    user_question = st.text_area("PDF에 대해 질문해보세요:", key="pdf_input", height=100)

    col1, col2 = st.columns([1, 1])
    with col1:
        if uploaded_file and st.session_state.api_key:
            if not st.session_state.pdf_file_id:
                try:
                    file_id = upload_pdf(uploaded_file)
                    st.session_state.pdf_file_id = file_id
                    assistant_id = create_assistant(file_id)
                    st.session_state.assistant_id = assistant_id
                    st.success("PDF 업로드 및 어시스턴트 준비 완료!")
                except Exception as e:
                    st.error(f"어시스턴트 생성 중 오류 발생: {e}")
    with col2:
        if st.button("Clear"):
            reset_session_state()
            st.session_state.pdf_input = ""

    if st.button("질문하기") and user_question:
        if not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        elif not st.session_state.assistant_id:
            st.warning("PDF 파일을 먼저 업로드하세요.")
        else:
            try:
                answer = chat_with_pdf(
                    st.session_state.assistant_id,
                    st.session_state.pdf_file_id,
                    user_question,
                )
                st.subheader("응답:")
                st.write(answer)
            except Exception as e:
                st.error(f"오류 발생: {e}")
