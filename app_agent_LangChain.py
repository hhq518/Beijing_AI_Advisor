# ========== 企业级新版 LangChain Agent（无报错版）==========
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from security_guard import validate_input
import os
import json

# ========== 1. 加载环境 ==========
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

# ========== 2. 初始化大模型 ==========
llm = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,
    model_name="qwen-turbo",
    temperature=0.1
)

# 初始化多模态模型专用客户端（和聊天客户端分开，避免冲突）
client = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,
    model_name="qwen-vl-max",
    temperature=0.3
)

# ========== 3. 工具定义（全部用 @tool 装饰器，格式统一）==========
@tool
def rag_search(query: str) -> str:
    """房产知识库检索，回答房产政策、房价、楼盘相关问题。

    Args:
        query: 用户的房产相关问题
    """
    return json.dumps({
        "query": query,
        "answer": "北京核心区房价稳定，刚需盘约5-7万/平，政策支持刚需购房..."
    }, ensure_ascii=False)

@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气情况。

    Args:
        city: 要查询天气的城市中文名
    """
    mock = {
        "北京": "晴，25℃，微风",
        "上海": "多云，28℃",
        "广州": "小雨，30℃"
    }
    return json.dumps({"city": city, "weather": mock.get(city, "暂无数据")}, ensure_ascii=False)

@tool
def multiply(a: int, b: int) -> str:
    """计算两个整数的乘积。

    Args:
        a: 第一个整数
        b: 第二个整数
    """
    return json.dumps({"result": a * b}, ensure_ascii=False)

@tool
def analyze_property_image(image_url: str) -> str:
    """分析房产户型图，描述户型结构、优缺点和适合的购房人群。

    Args:
        image_url: 户型图的公开可访问URL
    """
    try:
        # 调用多模态模型分析图片
        response = client.chat.completions.create(
            model="qwen-vl-max",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请详细分析这张户型图：描述房间数量、分布、优缺点，并给出适合的购房人群和大致估价建议。"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 图片分析失败：{str(e)}"

# ========== 4. 工具列表（直接用装饰器生成的工具）==========
tools = [rag_search, get_weather, multiply, analyze_property_image]

# ========== 5. 长期记忆配置 ==========
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    chat_memory=RedisChatMessageHistory(
        session_id="user_1",
        url="redis://localhost:6379/0"
    )
)

# ========== 6. 新版 Agent 专用 Prompt（必须包含 agent_scratchpad）==========
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是专业的北京房产AI助手，能根据用户问题调用工具回答，必须使用提供的工具，不要编造信息。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# ========== 7. 创建 Agent 和执行器 ==========
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True
)

# ========== 8. 启动交互 ==========
if __name__ == "__main__":
    print("=== 🔥 企业级新版 LangChain Agent 已启动 ===")
    while True:
        user_input = input("你：")
        if user_input.lower() in ["quit", "exit"]:
            print("再见！")
            break

        is_valid, msg = validate_input(user_input)
        if not is_valid:
            print(f"❌ 安全拦截：{msg}")
            continue

        res = agent_executor.invoke({"input": user_input})
        print(f"助手：{res['output']}\n")