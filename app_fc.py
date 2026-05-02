from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# --------------------------
# 0. 初始化（和你之前项目逻辑一致）
# --------------------------
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# --------------------------
# 1. RAG 知识库逻辑（直接复用 app_rag.py 的核心）
# --------------------------
# 这里简化了向量库部分，你可以直接把之前的RAG代码复制进来
# 核心逻辑：用户问房产相关问题时，调用知识库检索
def rag_search(query: str) -> str:
    """
    RAG知识库检索函数，查询房产相关信息
    """
    print(f"[RAG检索] 正在查询知识库：{query}")
    # 模拟从知识库中检索的结果（你可以替换成真实的ChromaDB检索逻辑）
    knowledge_base = {
        "朝阳公园附近小区": "朝阳公园附近热门小区包括棕榈泉国际公寓、泛海国际、观湖国际等，均价约11-14万/㎡，配套成熟，绿化率高。",
        "北京购房资格": "北京购房资格：京籍家庭限购2套，单身限购1套；非京籍需连续缴纳5年社保/个税，限购1套。"
    }
    return knowledge_base.get(query, "知识库中暂无相关房产信息")

# --------------------------
# 2. Function Calling 工具逻辑（复用 demo 里的天气工具）
# --------------------------
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息
    """
    print(f"[工具调用] 正在查询天气：{city}")
    weather_data = {
        "北京": "晴天，气温22℃，微风",
        "上海": "多云，气温25℃，南风",
        "广州": "小雨，气温28℃，东风"
    }
    return weather_data.get(city, f"暂无{city}的天气数据")

# 给AI的工具说明书（核心：告诉AI你有哪些工具）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "用于查询指定城市的实时天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "要查询天气的城市名称，比如：北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# --------------------------
# 3. 核心整合逻辑：自动判断走哪条路
# --------------------------
def handle_user_query(user_query: str) -> str:
    """
    统一处理用户问题，自动判断走RAG还是Function Calling
    """
    print(f"\n用户问题：{user_query}")

    # 第一步：先让AI判断，是否需要调用工具（Function Calling）
    print("\n--- 1. AI意图识别：判断是否需要调用工具 ---")
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": user_query}],
        tools=tools,
        tool_choice="auto"
    )
    message = response.choices[0].message

    # 情况A：AI判断需要调用工具（比如天气问题）
    if message.tool_calls:
        print("\n--- 2. 触发Function Calling路径 ---")
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        print(f"AI决定调用工具：{tool_name}，参数：{tool_args}")

        # 执行工具
        if tool_name == "get_weather":
            result = get_weather(city=tool_args["city"])

        # 把工具结果返回给AI，生成最终回答
        final_response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {"role": "user", "content": user_query},
                message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result
                }
            ]
        )
        return final_response.choices[0].message.content

    # 情况B：AI判断不需要调用工具，走RAG知识库路径
    else:
        print("\n--- 2. 触发RAG知识库路径 ---")
        # 调用RAG检索
        rag_result = rag_search(user_query)
        # 把检索结果给AI，生成专业回答
        prompt = f"""
        你是专业的北京房产分析师，根据以下知识库信息回答用户问题：
        知识库信息：{rag_result}
        用户问题：{user_query}
        """
        final_response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return final_response.choices[0].message.content

# --------------------------
# 4. 测试入口
# --------------------------
if __name__ == "__main__":
    print("=== 北京房产AI助手（RAG + Function Calling版） ===")
    print("你可以问房产相关问题，也可以问天气，我会自动判断处理！")
    print("输入 'exit' 退出程序\n")

    while True:
        # 等待用户输入问题
        user_input = input("请输入你的问题：")
        
        # 输入exit就退出
        if user_input.lower() == "exit":
            print("再见！")
            break
        
        # 调用处理函数，生成回答
        answer = handle_user_query(user_input)
        print(f"\nAI回答：{answer}\n")