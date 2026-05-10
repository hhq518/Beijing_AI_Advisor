# ========== 1. 导入依赖：和之前的项目保持一致 ==========
from openai import OpenAI
from dotenv import load_dotenv
from security_guard import validate_input
import os
import json
import redis    
# ========== Redis 长期记忆配置 ==========
r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True  # 自动转字符串，不用你处理编码
)
# ========== 2. 加载环境变量：和你之前的项目逻辑完全一致 ==========
load_dotenv()#把键值对塞进系统环境变量里
api_key = os.getenv("DASHSCOPE_API_KEY")# os去系统变量里面拿API Key和访问地址
base_url = os.getenv("DASHSCOPE_BASE_URL")

# 初始化OpenAI客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)# 创建一个能跟AI对话的客户端，就像你打开了一个聊天窗口，以后对话都通过它发

# ========== 3. 复制你之前的RAG检索函数：给Agent加上房产问答能力 ==========
def rag_search(query: str) -> str:
    """
    检索房产知识库，回答房产相关问题
    Args:
        query: 用户的房产相关问题，比如"北京房价走势"
    """
    # 直接复制之前项目里的rag_search函数，不用修改
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
# 新增工具1：计算器（乘法）
def multiply(a: int, b: int) -> str:
    """计算两个整数的乘积
    Args:
        a: 第一个整数
        b: 第二个整数
    """
    result = a * b
    return json.dumps({"a": a, "b": b, "result": result})

# 新增工具2：文本词数统计
def count_words(text: str) -> str:
    """统计一段文本的字符数量
    Args:
        text: 要统计的文本字符串
    """
    count = len(text.strip())
    return json.dumps({"text": text, "word_count": count})

def analyze_property_image(image_url: str) -> str:
    """
    房产图片分析工具：调用多模态模型解析户型图，给出专业分析
    """
    # 核心：用通义千问的多模态模型处理图片+文本
    response = client.chat.completions.create(
        model="qwen-vl-max",  # 必须用支持多模态的模型
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "帮我分析这张房产户型图，描述户型结构、朝向、优缺点，再给出估价建议"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    )
    return response.choices[0].message.content

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
    # 新增工具：计算器
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
    # 新增工具：词数统计
    {
        "type": "function",
        "function": {
            "name": "count_words",
            "description": "用户问文本词数/字符数统计问题时，调用这个工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要统计的文本字符串"}
                },
                "required": ["text"]
            }
        }
    },
    # 新增工具： 多模态图片
    {
        "type": "function",
        "function": {
            "name": "analyze_property_image",
            "description": "用户提供房产图片URL，需要分析户型、估价、优缺点时调用此工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "房产图片的URL地址"
                    }
                },
                "required": ["image_url"]
            }
        }
    }
]


# 工具映射表：模型决定调用哪个工具，我们就执行对应的函数
tool_map = {
    "rag_search": rag_search,
    "get_weather": get_weather,
    "multiply": multiply,
    "count_words": count_words,
    "analyze_property_image": analyze_property_image
}
# ========== Redis 长期记忆函数 ==========
def load_redis_memory():
    """从 Redis 加载历史对话"""
    history = r.get("chat_history")
    return json.loads(history) if history else []

def save_redis_memory(history):
    filtered_history = []
    for msg in history:
        # 关键：把所有对象都转成字典，不管是普通dict还是OpenAI对象
        if hasattr(msg, "model_dump"):
            msg_dict = msg.model_dump()
        elif hasattr(msg, "to_dict"):
            msg_dict = msg.to_dict()
        else:
            msg_dict = dict(msg)
        
        # 只保留用户和助手的对话消息
        if msg_dict.get("role") in ["user", "assistant"]:
            filtered_history.append(msg_dict)
    
    # 保存到Redis
    r.set("chat_history", json.dumps(filtered_history, ensure_ascii=False))

# ========== 6. 核心：实现ReAct Agent循环，自动路由用户意图 ==========
# 原理：这就是你面试话术里说的「思考-行动-观察-再思考」循环
def run_agent(query: str):
    """
    运行ReAct Agent循环，自动路由用户意图并调用对应工具
    Args:
        query: 用户输入的问题
    Returns:
        final_answer: Agent最终返回的答案
    """
    print(f"\n=== 用户问题：{query} ===")

    # 加载Redis里的历史对话（纯字典，避免对象序列化问题）
    messages = load_redis_memory()
    # 追加当前用户问题到对话历史
    messages.append({"role": "user", "content": query})

    final_answer = ""
    # ReAct循环：思考→行动→观察→再思考
    while True:
        # 调用大模型，让模型决定是否调用工具
        try:
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                tools=tools,
                tool_choice="auto"  # 让模型自动决定是否调用工具
            )
        except Exception as e:
            final_answer = f"Agent执行出错：{str(e)}"
            print(f"[Error] {final_answer}")
            messages.append({"role": "assistant", "content": final_answer})
            save_redis_memory(messages)
            return final_answer

        response_message = response.choices[0].message

        # 情况1：模型不需要调用工具，直接返回最终答案
        if not response_message.tool_calls:
            final_answer = response_message.content
            print(f"[Final Answer] {final_answer}")
            # 将模型回答转为字典并追加到历史
            messages.append(response_message.model_dump())
            # 保存更新后的对话到Redis
            save_redis_memory(messages)
            return final_answer

        # 情况2：模型需要调用工具，执行工具调用逻辑
        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            # 解析工具参数（容错：避免JSON解析失败）
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}
                print(f"[Warning] 工具参数解析失败：{tool_call.function.arguments}")

            print(f"[Action] 调用工具：{tool_name}，参数：{tool_args}")

            # 执行工具函数（容错：避免工具不存在/参数错误）
            try:
                tool_result = tool_map[tool_name](**tool_args)
            except Exception as e:
                tool_result = json.dumps({"error": f"工具执行失败：{str(e)}"})
            print(f"[Observation] 工具返回：{tool_result}")

            # 将工具调用结果追加到对话历史，供模型后续思考
            # 1. 追加模型的工具调用指令到历史
            messages.append(response_message.model_dump())
            # 2. 追加工具返回结果到历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_result
            })


# ========== 7. 运行测试：验证意图路由是否生效 ==========
if __name__ == "__main__":
    print("=== 多工具Agent已启动，输入问题开始对话，输入 quit 退出 ===")
    print("----------------------------------------")
    while True:
        user_input = input("请输入问题：")
        if user_input.strip().lower() == "quit":
            print("Agent：再见👋")
            break
        #安全校验 企业级 AI 应用标准安全架构
        is_valid, msg = validate_input(user_input)
        if not is_valid:
            print(f"❌ 安全拦截：{msg}")
            continue  # 直接跳过，不进入 Agent

        print("----------------------------------------")
        run_agent(user_input)  # 改成和你定义的函数名一致
        print("----------------------------------------")