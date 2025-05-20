import openai
import streamlit as st
import pdfplumber
from duckduckgo_search import DDGS

def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
        combined = "\n\n".join(f"{r['title']}\n{r['body']}" for r in results)
        return combined if combined else "검색 결과를 찾을 수 없습니다."

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def extract_text_from_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8")

def get_chat_response(api_key, messages):
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

st.set_page_config(page_title="GPT 챗봇", layout="wide")
st.title("GPT-4o 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 웹 검색, PDF 분석, 코드 파일 분석이 가능한 GPT-4 도우미입니다."}
    ]

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.text_input("OpenAI API 키를 입력하세요", type="password", key="api_key")

if not st.session_state.api_key:
    st.warning("API 키를 입력해야 챗봇을 사용할 수 있습니다.")
    st.stop()

pdf_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])
txt_file = st.file_uploader("TXT 파일 업로드", type=["txt"])

user_input = st.text_area("질문을 입력하세요", height=100, key="user_input")
submit = st.button("질문하기")

if st.button("대화 초기화"):
    st.session_state.messages = [
        {"role": "system", "content": "당신은 웹 검색, PDF 분석, 코드 파일 분석이 가능한 GPT-4 도우미입니다."}
    ]
    st.session_state.user_input = ""
    st.experimental_rerun()

if submit and user_input:
    context = ""

    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        context += "\n\n[PDF 파일 내용]\n" + pdf_text

    if txt_file:
        txt_text = extract_text_from_txt(txt_file)
        context += "\n\n[TXT 파일 내용]\n" + txt_text

    web_result = search_web(user_input)
    context += "\n\n[웹 검색 결과]\n" + web_result

    full_prompt = f"{user_input}\n\n[참고 자료]\n{context}"

    st.session_state.messages.append({"role": "user", "content": full_prompt})

    with st.spinner("응답을 생성 중입니다..."):
        assistant_reply = get_chat_response(st.session_state.api_key, st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    st.session_state.user_input = ""

for msg in st.session_state.messages[1:]:
    st.markdown(f"{msg['role'].capitalize()}: {msg['content']}")
