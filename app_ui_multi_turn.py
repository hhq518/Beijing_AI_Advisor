import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# --------------------------
# 0. 初始化配置（和之前的项目一致）
# --------------------------
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# --------------------------
# 1. 关键：初始化聊天历史记录
# --------------------------
# 这是多轮对话的核心！用st.session_state来保存聊天记录，刷新页面也不会丢
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------
# 2. Streamlit页面设置
# --------------------------
st.set_page_config(page_title="北京房产AI顾问（多轮对话版）", layout="wide")
st.title("🏠 北京房产AI顾问 - 多轮对话版")

# --------------------------
# 3. 把历史聊天记录显示在页面上
# --------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --------------------------
# 4. 用户输入 + 多轮对话逻辑
# --------------------------
if prompt := st.chat_input("请输入你的房产问题..."):
    # 1. 把用户的新问题，加入聊天历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 把【完整的聊天历史】一起发给AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # 核心区别：这里不再只发当前用户问题，而是发整个st.session_state.messages
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=st.session_state.messages,
            stream=True
        )

        # 流式输出AI回答
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    # 3. 把AI的回答也加入聊天历史，下一轮对话就能用上
    st.session_state.messages.append({"role": "assistant", "content": full_response})