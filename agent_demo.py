from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os
import json

# ========== 1. 环境初始化 ==========
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

# 初始化大模型（兼容通义千问）
llm = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,
    model_name="qwen-turbo",
    temperature=0.1
)

# ========== 2. 工具定义 ==========
def get_weather(city: str) -> str:
    """获取指定城市的实时天气（模拟API）
    Args:
        city: 要查询的城市中文名
    """
    try:
        mock_weather = {
            "北京": "晴，25℃，微风",
            "上海": "多云，28℃，东风",
            "广州": "小雨，30℃，南风"
        }
        result = {
            "city": city,
            "weather": mock_weather.get(city, "未知城市，无法查询天气"),
            "status": "success"
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"}, ensure_ascii=False)

def count_word_frequency(text: str) -> str:
    """统计文本词频，返回出现次数最多的前3个词
    Args:
        text: 要统计的文本字符串
    """
    try:
        if not text.strip():
            raise ValueError("文本不能为空")
        words = text.split()
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1
        top3 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
        return json.dumps({"top3_words": top3, "status": "success"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"}, ensure_ascii=False)

# 注册工具（LangChain 标准格式）
tools = [
    Tool(
        name="get_weather",
        description="获取城市天气，参数是城市中文名，当用户询问天气相关问题时调用",
        func=get_weather
    ),
    Tool(
        name="count_word_frequency",
        description="统计文本词频，返回出现次数最多的前3个词，当用户要求统计高频词时调用",
        func=count_word_frequency
    )
]

# ========== 3. 记忆模块 ==========
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"
)

# ========== 4. 创建稳定版 Agent ==========
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,  # 改用更宽松的格式，和通义千问兼容性更好
    verbose=True,
    memory=memory,
    handle_parsing_errors=True,
    max_iterations=5
)

# ========== 5. 交互式提问循环 ==========
if __name__ == "__main__":
    print("=== 智能助手启动！输入 'exit' 或 'quit' 可退出 ===")
    print("你可以问我：")
    print("1. 天气类问题（比如：北京今天天气怎么样？）")
    print("2. 词频统计（比如：帮我统计'我 我 今天 今天 北京 北京'的高频词）")
    print("3. 多轮对话（比如：根据刚才的天气写一句文案）\n")

    while True:
        # 获取用户输入
        user_input = input("你：")
        
        # 退出指令
        if user_input.lower() in ["exit", "quit", "再见", "退出"]:
            print("助手：再见！")
            break
        
        # 空输入跳过
        if not user_input.strip():
            continue

        # 调用 Agent 回答
        try:
            response = agent_executor.invoke({"input": user_input})
            print(f"助手：{response['output']}\n")
        except Exception as e:
            print(f"助手：哎呀，出了点小问题，错误信息：{str(e)}\n")