# 导入阿里云百炼的OpenAI兼容客户端，和你之前项目用的是同一个
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# --------------------------
# 1. 加载环境变量（和你之前的项目逻辑一样）
# --------------------------
# 从.env文件里读取API_KEY和BASE_URL，避免把敏感信息写死在代码里
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL")
)

# --------------------------
# 2. 定义我们的“工具函数”（Function Calling的核心）
# --------------------------
# 这就是AI未来会调用的工具，你可以把它理解成AI的“外接工具包”
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息（这里我们用模拟数据，实际项目可以换成真实API）
    参数:
        city: 要查询天气的城市名称
    返回:
        该城市的天气描述字符串
    """
    print(f"[工具调用] 正在查询 {city} 的天气...")
    # 模拟真实天气API返回的数据
    weather_data = {
        "北京": "晴天，气温22℃，微风",
        "上海": "多云，气温25℃，南风",
        "广州": "小雨，气温28℃，东风"
    }
    return weather_data.get(city, f"暂无{city}的天气数据")

# --------------------------
# 3. 告诉AI：我有哪些工具、每个工具是干嘛的（关键步骤！）
# --------------------------
# 这一段就是给AI的“工具说明书”，AI会根据这个说明书，判断什么时候该调用哪个工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",  # 工具的名字，必须和上面的函数名完全一致
            "description": "用于查询指定城市的实时天气信息",  # 给AI看的工具用途说明，AI会根据这个判断什么时候用
            "parameters": {  # 工具需要的参数说明，AI会根据这个生成调用参数
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "要查询天气的城市名称，比如：北京、上海"
                    }
                },
                "required": ["city"]  # 这个参数是必填的
            }
        }
    }
]

# --------------------------
# 4. 主流程：用户提问 → AI判断 → 工具调用 → 回答生成
# --------------------------
def main():
    # 用户的问题，这就是我们的“触发词”
    user_query = "今天北京天气怎么样？"
    print(f"用户问题：{user_query}")

    # 第一步：先把用户问题发给AI，让它判断要不要调用工具
    print("\n--- 1. 发送用户问题给AI，判断意图 ---")
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": user_query}],
        tools=tools,  # 把我们定义的工具说明书传给AI
        tool_choice="auto"  # 让AI自己判断要不要调用工具，不用我们手动控制
    )

    # 拿到AI的回复，这里AI不会直接回答天气，而是会给我们一个“调用工具的指令”
    message = response.choices[0].message

    # 第二步：检查AI有没有决定调用工具
    if message.tool_calls:
        print("\n--- 2. AI判断需要调用工具 ---")
        # 取出AI生成的工具调用指令
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        # AI给我们生成的参数，比如 {"city": "北京"}
        tool_args = json.loads(tool_call.function.arguments)

        print(f"AI决定调用工具：{tool_name}，参数：{tool_args}")

        # 第三步：我们执行工具函数，拿到真实数据
        print("\n--- 3. 执行工具函数，获取结果 ---")
        if tool_name == "get_weather":
            weather_result = get_weather(city=tool_args["city"])
            print(f"工具返回结果：{weather_result}")

        # 第四步：把工具返回的结果，再发给AI，让它整理成自然语言回答
        print("\n--- 4. 把工具结果返回给AI，生成最终回答 ---")
        final_response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {"role": "user", "content": user_query},
                message,  # 把AI之前的工具调用请求也带上，保持对话上下文
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": weather_result
                }
            ]
        )

        # 拿到AI整理后的最终回答
        final_answer = final_response.choices[0].message.content
        print(f"\nAI最终回答：{final_answer}")

    else:
        # 如果AI判断不需要调用工具，就直接回答
        print("\nAI直接回答（不需要调用工具）：")
        print(message.content)

# 运行主函数
if __name__ == "__main__":
    main()