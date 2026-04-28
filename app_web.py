import streamlit as st
from app_rag import init_knowledge_base, rag_answer  # 直接复用RAG核心逻辑

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="北京房产AI助手",
    page_icon="🏠",
    layout="wide"
)

# --------------------------
# 初始化（只运行一次）
# --------------------------
@st.cache_resource
def load_knowledge_base():
    """缓存知识库，避免每次刷新都重新加载"""
    return init_knowledge_base()

# 加载知识库
with st.spinner("正在初始化知识库，请稍候..."):
    db = load_knowledge_base()

# --------------------------
# 页面标题和说明
# --------------------------
st.title("🏠 北京房产AI智能分析助手")
st.markdown("""
> 基于本地知识库的RAG问答助手，为您提供北京房产政策、市场数据、房源信息的专业咨询服务。
> 提示：问题越具体，回答越精准，比如“朝阳公园附近的房源单价大概是多少？”
""")

# --------------------------
# 对话历史
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------
# 接收用户输入
# --------------------------
if prompt := st.chat_input("请输入您的问题..."):
    # 保存用户问题
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用RAG生成回答
    with st.chat_message("assistant"):
        with st.spinner("正在分析知识库并生成回答..."):
            response = rag_answer(prompt, db)
            st.markdown(response)

    # 保存AI回答
    st.session_state.messages.append({"role": "assistant", "content": response})