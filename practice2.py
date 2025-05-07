import streamlit as st
import openai
import os
from io import BytesIO

st.set_page_config(page_title="ChatPDF GPT-4o", layout="centered")

# 세션 상태 초기화
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "pdf_file_id" not in st.session_state:
    st.session_state.pdf_file_id = None
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# 사이드바
page = st.sidebar.selectbox("페이지 선택", ["Q&A", "Chat", "Chatbot", "ChatPDF"])

st.session_state.api_key = st.sidebar.text_input(
    "OpenAI API Key 입력",
    type="password",
    value=st.session_state.api_key,
)

# OpenAI 클라이언트 생성
def get_client():
    return openai.OpenAI(api_key=st.session_state.api_key)

# PDF 파일 업로드 및 임베딩
def upload_pdf(file):
    client = get_client()
    st.info("PDF 파일 업로드 중...")
    uploaded = client.files.create(file=(file.name, file), purpose="assistants")
    return uploaded.id

# Assistant 생성
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

# Thread 생성 및 메시지 전송
def chat_with_pdf(assistant_id, file_id, user_message):
    client = get_client()

    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # 메시지 추가
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_message,
    )

    # 실행 요청
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
        latest_response = messages.data[0].content[0].text.value
        return latest_response

# 페이지: ChatPDF
if page == "ChatPDF":
    st.title("ChatPDF - PDF 기반 챗봇")

    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요 (1개만)", type=["pdf"])

    if st.button("Clear"):
        st.session_state.pdf_file_id = None
        st.session_state.assistant_id = None
        st.session_state.thread_id = None
        st.success("파일 및 대화 기록이 초기화되었습니다.")

    if uploaded_file and st.session_state.api_key:
        if not st.session_state.pdf_file_id:
            file_id = upload_pdf(uploaded_file)
            st.session_state.pdf_file_id = file_id
            assistant_id = create_assistant(file_id)
            st.session_state.assistant_id = assistant_id
            st.success("PDF 업로드 및 어시스턴트 준비 완료!")

    if st.session_state.pdf_file_id:
        user_question = st.text_input("PDF에 대해 질문해보세요:")
        if user_question:
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
        st.warning("API Key를 입력하세요.")
