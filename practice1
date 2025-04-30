import streamlit as st
import openai

st.set_page_config(page_title="GPT-4.1 Mini QA", layout="centered")
st.title("🧠 GPT-4.1 Mini 질문 응답기")

# API Key 입력받기
api_key = st.text_input("🔐 OpenAI API Key를 입력하세요:", type="password")

# 질문 입력받기
user_input = st.text_area("❓ 질문을 입력하세요:", height=150)

# 답변 생성 버튼
if st.button("답변 생성"):
    if not api_key:
        st.warning("⚠️ API Key를 입력해주세요.")
    elif not user_input.strip():
        st.warning("⚠️ 질문을 입력해주세요.")
    else:
        try:
            openai.api_key = api_key

            with st.spinner("GPT-4.1 Mini가 답변을 생성 중입니다..."):
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",  # 핵심 부분: GPT-4.1 mini 모델 사용
                    messages=[
                        {"role": "system", "content": "당신은 유용하고 친절한 AI 어시스턴트입니다."},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
                answer = response["choices"][0]["message"]["content"]
                st.success("✅ GPT의 답변:")
                st.write(answer)

        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")
