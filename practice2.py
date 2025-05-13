import streamlit as st
import openai
import time
import PyPDF2
import numpy as np

st.set_page_config(page_title="GPT-4o Mini Web App", layout="centered")

# session_state 초기화
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
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None
if "clear_flag" not in st.session_state:
    st.session_state.clear_flag = False
if "qa_input" not in st.session_state:
    st.session_state.qa_input = ""
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""
if "library_input" not in st.session_state:
    st.session_state.library_input = ""
if "pdf_input" not in st.session_state:
    st.session_state.pdf_input = ""
if "pdf_chunks" not in st.session_state:
    st.session_state.pdf_chunks = []
if "pdf_embeddings" not in st.session_state:
    st.session_state.pdf_embeddings = []

page = st.sidebar.selectbox("페이지 선택", ["Q&A", "Chat", "Chatbot", "ChatPDF"])

st.session_state.api_key = st.sidebar.text_input(
    "OpenAI API Key 입력",
    type="password",
    value=st.session_state.api_key,
)

if st.sidebar.button("API Key 초기화"):
    st.session_state.api_key = ""

def get_client():
    return openai.OpenAI(api_key=st.session_state.api_key)

@st.cache_data
def get_response(api_key: str, messages: list) -> str:
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def load_rules():
    try:
        with open("library_rules.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "도서관 규정 파일을 찾을 수 없습니다."

def extract_text_from_pdf(file) -> str:
    reader = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def chunk_text(text: str, max_tokens=500) -> list[str]:
    sentences = text.split(". ")
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk + sentence) < max_tokens:
            chunk += sentence + ". "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + ". "
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def embed_chunks(chunks: list[str]):
    client = get_client()
    clean_chunks = [chunk for chunk in chunks if isinstance(chunk, str) and chunk.strip()]
    if not clean_chunks:
        raise ValueError("입력할 유효한 텍스트 청크가 없습니다.")
    response = client.embeddings.create(
        input=clean_chunks,
        model="text-embedding-3-small"
    )
    return [item.embedding for item in response.data]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_similar_chunks(query: str, chunks: list[str], embeddings: list[list[float]], k=3):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query는 비어있거나 유효하지 않습니다.")
    
    client = get_client()
    query_embedding = client.embeddings.create(
        input=[query],
        model="text-embedding-3-small"
    ).data[0].embedding
    
    similarities = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    top_indices = np.argsort(similarities)[::-1][:k]
    return "\n\n".join([chunks[i] for i in top_indices])

def ask_pdf_bot(query: str, context: str):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "다음 문서를 참고하여 질문에 답하세요:\n" + context},
            {"role": "user", "content": query}
        ]
    )
    return response.choices[0].message.content.strip()

def get_single_response(prompt: str):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "당신은 친절한 AI 비서입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def reset_session_state():
    st.session_state.clear_flag = False
    st.session_state.chat_history = []
    st.session_state.library_chat_history = []
    st.session_state.pdf_file_id = None
    st.session_state.assistant_id = None
    st.session_state.thread_id = None
    st.session_state.vector_store_id = None
    st.session_state.qa_input = ""
    st.session_state.chat_input = ""
    st.session_state.library_input = ""
    st.session_state.pdf_input = ""
    st.session_state.pdf_chunks = []
    st.session_state.pdf_embeddings = []

if page == "Q&A":
    st.title("GPT-4o Mini 질문 응답기")
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    st.session_state.qa_input = st.text_area("질문을 입력하세요:", value=st.session_state.qa_input, height=100)
    if st.button("질문하기"):
        if st.session_state.qa_input.strip() == "":
            st.warning("질문을 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            with st.spinner("응답 생성 중..."):
                messages = [
                    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
                    {"role": "user", "content": st.session_state.qa_input}
                ]
                answer = get_response(st.session_state.api_key, messages)
                st.subheader("응답:")
                st.write(answer)

elif page == "Chat":
    st.title("GPT-4o Mini 챗봇")
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    st.session_state.chat_input = st.text_area("메시지를 입력하세요:", value=st.session_state.chat_input, height=100)
    if st.button("질문하기"):
        if st.session_state.chat_input.strip() == "":
            st.warning("메시지를 입력하세요.")
        elif not st.session_state.api_key:
            st.warning("API Key를 입력하세요.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": st.session_state.chat_input})
            messages = [{"role": "system", "content": "당신은 친절하고 유용한 챗봇입니다."}] + st.session_state.chat_history
            assistant_reply = get_response(st.session_state.api_key, messages)
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.chat_history:
        role = "사용자" if msg["role"] == "user" else "GPT"
        st.markdown(f"**{role}:** {msg['content']}")

elif page == "Chatbot":
    st.title("국립부경대학교 도서관 챗봇")
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Clear"):
            reset_session_state()

    st.session_state.library_input = st.text_area("도서관에 대해 궁금한 점을 입력하세요:", value=st.session_state.library_input, height=100)
    library_regulations = load_rules()
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
            assistant_reply = get_response(st.session_state.api_key, messages)
            st.session_state.library_chat_history.append({"role": "assistant", "content": assistant_reply})
    for msg in st.session_state.library_chat_history:
        role = "사용자" if msg["role"] == "user" else "도서관 챗봇"
        st.markdown(f"**{role}:** {msg['content']}")

elif page == "ChatPDF":
    st.title("ChatPDF - PDF 기반 챗봇")

    if "pdf_chat_history" not in st.session_state:
        st.session_state.pdf_chat_history = []
    if "pdf_input" not in st.session_state:
        st.session_state.pdf_input = ""

    uploaded_file = st.file_uploader("PDF 파일 업로드", type="pdf")

    if st.button("Clear PDF", key="clear_button_chatpdf"):
        st.session_state.pdf_chunks = []
        st.session_state.pdf_embeddings = []
        st.session_state.pdf_input = ""
        st.session_state.pdf_chat_history = []
        st.success("PDF 데이터 및 대화 기록이 초기화되었습니다.")

    if uploaded_file and st.session_state.api_key:
        with st.spinner("PDF 분석 중..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            chunks = chunk_text(raw_text)
            embeddings = embed_chunks(chunks)

            st.session_state.pdf_chunks = chunks
            st.session_state.pdf_embeddings = embeddings
            st.success(f"{len(chunks)}개의 청크로 분할 및 임베딩 완료!")

    if st.session_state.pdf_chunks:
        st.session_state.pdf_input = st.text_input("PDF 내용 기반 질문을 입력하세요:", value=st.session_state.pdf_input)
        if st.session_state.pdf_input:
            with st.spinner("응답 생성 중..."):
                context = search_similar_chunks(
                    st.session_state.pdf_input,
                    st.session_state.pdf_chunks,
                    st.session_state.pdf_embeddings
                )
                answer = ask_pdf_bot(st.session_state.pdf_input, context)
                st.session_state.pdf_chat_history.append(
                    {"user": st.session_state.pdf_input, "bot": answer}
                )

    for chat in st.session_state.get("pdf_chat_history", []):
        st.markdown(f"**사용자:** {chat['user']}")
        st.markdown(f"**GPT 응답:** {chat['bot']}")
        
