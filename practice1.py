import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="GPT-4.1 Mini 질문 응답기", layout="centered")
st.title("GPT-4.1 Mini 질문 응답기")

# API Key 입력
api_key = st.text_input("OpenAI API Key를 입력하세요:", type="password")

# 질문 입력
user_input = st.text_area("질문을 입력하세요:", height=150)

# 버튼 클릭 시 처리
if st.button("답변 생성"):
    if not api_key:
        st.warning("API Key를 입력해주세요.")
    elif not user_input.strip():
        st.warning("질문을 입력해주세요.")
    else:
        try:
            # OpenAI 클라이언트 생성
            client = OpenAI(api_key=api_key)

            # GPT-4.1 Mini로 응답 생성
            with st.spinner("GPT가 답변을 생성 중입니다..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 사실만을 답하는 정확한 AI입니다. 꾸며내거나 지어내어서 답변을 하지 말고, 모르거나 애매한 내용이라면 '잘 모르겠습니다.'라고 명시하고, 지어낸 내용이면 '지어낸 내용입니다.'라고 명시하세요."},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )

                answer = response.choices[0].message.content
                st.success("GPT의 답변:")
                st.write(answer)

        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")
