import openai
import streamlit as st
from datetime import datetime
import base64
import random
import time

# OpenAI API 키 설정
openai.api_key = "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"

# 세션 초기화
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = []

# 페이지 설정 함수
def main():
    st.set_page_config(
        page_title="Chatbot",
        page_icon="https://cdn-icons-png.flaticon.com/128/14898/14898163.png",
    )
    st.markdown("# Chatbot")

    # 이전 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("Ask me anything!"):
        # 사용자 메시지 저장 및 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 응답 생성 및 표시
        with st.chat_message("assistant"):
            stream = openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = ""
            for chunk in stream:
                response_chunk = chunk["choices"][0]["delta"].get("content", "")
                response += response_chunk
                st.write(response_chunk, end="")  # 실시간 출력
            st.write(response)  # 최종 응답 출력

        st.session_state.messages.append({"role": "assistant", "content": response})

# 메인 실행
if __name__ == "__main__":
    main()