# ========== 1. 导入依赖：和你之前的项目完全一致 ==========
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# ========== 2. 加载环境变量 ==========
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

# 初始化OpenAI客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# ========== 3. 定义三个工具：给Agent装上“工具箱” ==========
# 工具1：天气查询
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

# 工具2：计算器（乘法）
def multiply(a: int, b: int) -> str:
    """计算两个整数的乘积
    Args:
        a: 第一个整数
        b: 第二个整数
    """
    result = a * b
    return json.dumps({"a": a, "b": b, "result": result})

# 工具3：文本词数统计
def count_words(text: str) -> str:
    """统计一段文本的单词数量
    Args:
        text: 要统计的文本字符串
    """
    words = text.split()
    count = len(words)
    return json.dumps({"text": text, "word_count": count})

# ========== 4. 关键：把工具包装成Agent能识别的格式 ==========
# 原理：每个工具都要有清晰的描述，告诉Agent“什么时候用它”
tools = [
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
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "用户问乘法计算问题时，调用这个工具计算两个数的乘积",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "第一个整数"},
                    "b": {"type": "integer", "description": "第二个整数"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_words",
            "description": "用户问文本词数统计问题时，调用这个工具统计单词数量",
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

# 工具映射表：Agent选好工具后，我们执行对应的函数
tool_map = {
    "get_weather": get_weather,
    "multiply": multiply,
    "count_words": count_words
}

# ========== 5. 核心：实现多工具编排的ReAct循环 ==========
# 原理：Agent会根据问题自动判断用哪个工具，全程不用你干预
def run_orchestration_agent(query: str):
    print(f"\n=== 用户问题：{query} ===")
    messages = [{"role": "user", "content": query}]
    
    while True:
        # 1. Thought：Agent分析问题，决定用哪个工具
        print("\n[Thought] Agent正在分析用户意图...")
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"  # 自动选择工具，这就是编排的核心
        )
        response_message = response.choices[0].message
        
        # 2. 如果不需要调用工具，直接输出答案
        if not response_message.tool_calls:
            print(f"[Final Answer] {response_message.content}")
            return response_message.content
        
        # 3. Action：执行Agent选好的工具
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"[Action] 调用工具：{tool_name}，参数：{tool_args}")
            
            # 4. Observation：拿到工具结果，喂给Agent继续思考
            tool_result = tool_map[tool_name](**tool_args)
            print(f"[Observation] 工具返回：{tool_result}")
            
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_result
            })

# ========== 6. 测试运行：验证自动选工具的效果 ==========
if __name__ == "__main__":
    print("=== 开始测试多工具编排Agent ===")
    
    # 测试1：天气问题 → 自动选get_weather
    run_orchestration_agent("今天北京天气怎么样？")
    
    # 测试2：乘法问题 → 自动选multiply
    run_orchestration_agent("123乘以456等于多少？")
    
    # 测试3：词数统计 → 自动选count_words
    run_orchestration_agent("这段文字有多少个词：人工智能正在改变世界")