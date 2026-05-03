from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# ========== 1. 加载环境变量，和你之前的项目逻辑完全一致 ==========
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

# 初始化OpenAI客户端（直接用Function Calling，不依赖LangChain）
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# ========== 2. 定义工具（和之前一样，完全不变） ==========
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

# 把工具定义成OpenAI能识别的格式
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的实时天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "要查询的城市名，比如北京、上海"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_word_frequency",
            "description": "统计文本的词频，返回出现次数最多的前3个词",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要统计的文本字符串"}
                },
                "required": ["text"]
            }
        }
    }
]

# 工具映射表，方便调用
tool_map = {
    "get_weather": get_weather,
    "count_word_frequency": count_word_frequency
}

# ========== 3. 手动实现ReAct循环（核心！） ==========
def run_react_agent(query: str):
    print(f"\n=== 用户问题：{query} ===")
    messages = [{"role": "user", "content": query}]
    
    while True:
        # 1. 调用大模型，获取思考/工具调用决策
        print("\n[Thought] 模型正在思考...")
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        response_message = response.choices[0].message
        
        # 如果模型不调用工具，直接输出最终答案，结束循环
        if not response_message.tool_calls:
            print(f"[Final Answer] {response_message.content}")
            return response_message.content
        
        # 2. 解析工具调用（Action）
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"[Action] 调用工具：{tool_name}，参数：{tool_args}")
            
            # 3. 执行工具，获取Observation
            tool_result = tool_map[tool_name](**tool_args)
            print(f"[Observation] 工具返回：{tool_result}")
            
            # 把工具调用和结果加入对话历史，让模型继续思考
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_result
            })

# ========== 4. 测试运行 ==========
if __name__ == "__main__":
    print("=== 开始测试ReAct Agent ===")
    
    # 测试1：调用天气工具
    run_react_agent("北京今天的天气怎么样？")

    # 测试2：调用词频工具
    run_react_agent("统计一下这句话里的高频词：我 我 我 今天 今天 今天 去 去 去 北京 北京 北京 玩")

    # 测试3：多轮工具调用（先查天气，再写文案）
    run_react_agent("北京今天的天气怎么样？根据天气写一句适合发朋友圈的文案")