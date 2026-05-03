# ========== 1. 导入依赖：和你之前的项目保持一致 ==========
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# ========== 2. 加载环境变量：和你之前的项目逻辑完全一致 ==========
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

# 初始化OpenAI客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# ========== 3. 复制你之前的RAG检索函数：给Agent加上房产问答能力 ==========
def rag_search(query: str) -> str:
    """
    检索房产知识库，回答房产相关问题
    Args:
        query: 用户的房产相关问题，比如"北京房价走势"
    """
    # 这里直接复制你之前项目里的rag_search函数，不用修改
    # （如果你的rag_search是在别的文件里，也可以用from app_rag import rag_search导入）
    # 示例：模拟知识库检索结果
    return json.dumps({
        "query": query,
        "answer": "根据知识库检索，北京核心区房价走势稳定，刚需盘均价约5-7万/平..."
    })

# ========== 4. 复制之前的工具：给Agent加上天气、词频能力 ==========
def get_weather(city: str) -> str:
    """获取指定城市的实时天气
    Args:
        city: 要查询的城市名，比如"北京"、"上海"
    """
    mock_weather = {
        "北京": "晴，25℃，微风",
        "上海": "多云，28℃，东风",
        "广州": "小雨，30℃，南风"
    }
    return json.dumps({"city": city, "weather": mock_weather.get(city, "未知城市，无法查询天气")})

def count_word_frequency(text: str) -> str:
    """统计文本的词频，返回出现次数最多的前3个词
    Args:
        text: 要统计的文本字符串
    """
    words = text.split()
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    top3 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
    return json.dumps({"top3_words": top3})

# ========== 5. 关键步骤：把所有工具包装成Agent能识别的格式 ==========
# 原理：OpenAI的Function Calling需要固定格式，告诉模型每个工具的作用、参数
tools = [
    # 工具1：房产知识库检索
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "用户问房产相关问题时，调用这个工具检索知识库",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户的房产相关问题"}
                },
                "required": ["query"]
            }
        }
    },
    # 工具2：天气查询
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "用户问天气相关问题时，调用这个工具查询实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "要查询天气的城市名"}
                },
                "required": ["city"]
            }
        }
    },
    # 工具3：词频统计
    {
        "type": "function",
        "function": {
            "name": "count_word_frequency",
            "description": "用户问文本统计、词频相关问题时，调用这个工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要统计词频的文本"}
                },
                "required": ["text"]
            }
        }
    }
]

# 工具映射表：模型决定调用哪个工具，我们就执行对应的函数
tool_map = {
    "rag_search": rag_search,
    "get_weather": get_weather,
    "count_word_frequency": count_word_frequency
}

# ========== 6. 核心：实现ReAct Agent循环，自动路由用户意图 ==========
# 原理：这就是你面试话术里说的「思考-行动-观察-再思考」循环
def run_agent(query: str):
    print(f"\n=== 用户问题：{query} ===")
    messages = [{"role": "user", "content": query}]
    
    while True:
        # 1. 思考：模型收到问题，判断要不要调用工具、调用哪个工具
        print("\n[Thought] 模型正在分析用户意图...")
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"  # 自动判断是否调用工具
        )
        response_message = response.choices[0].message
        
        # 2. 如果不需要调用工具，直接输出答案（比如无关问题）
        if not response_message.tool_calls:
            print(f"[Final Answer] {response_message.content}")
            return response_message.content
        
        # 3. 行动：调用模型选择的工具
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"[Action] 调用工具：{tool_name}，参数：{tool_args}")
            
            # 4. 观察：执行工具，获取结果
            tool_result = tool_map[tool_name](**tool_args)
            print(f"[Observation] 工具返回：{tool_result}")
            
            # 把工具结果喂给模型，让它继续思考/生成最终答案
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_result
            })

# ========== 7. 运行测试：验证意图路由是否生效 ==========
if __name__ == "__main__":
    print("=== 开始测试全功能Agent ===")
    
    # 测试1：房产问题 → 自动走RAG检索
    run_agent("北京现在房价怎么样？")
    
    # 测试2：天气问题 → 自动调用天气工具
    run_agent("北京今天的天气怎么样？")
    
    # 测试3：无关问题 → 直接回答
    run_agent("今天吃什么？")
    
    # 测试4：复杂问题（多轮调用）
    run_agent("北京今天的天气怎么样？根据天气推荐一个适合看房的日子")