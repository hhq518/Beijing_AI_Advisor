#加载环境与初始化
from openai import OpenAI
from dotenv import load_dotenv
import os
import redis
import json

# ========== 加载环境变量 ==========
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

# 初始化OpenAI客户端
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)
# 导入redis库
# 初始化存储
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
# 加载历史对话（关键步骤）
def load_memory():
    history = r.get("chat_history")
    return json.loads(history) if history else []
# 保存对话记录
def save_memory(history):
    r.set("chat_history", json.dumps(history))
#带记忆的对话主逻辑
def chat_with_memory(query: str):
    # 1. 加载历史对话
    history = load_memory()
    
    # 2. 把新问题加进对话历史
    history.append({"role": "user", "content": query})
    
    # 3. 调用模型回答
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=history
    )
    answer = response.choices[0].message.content
    
    # 4. 把回答也加进对话历史
    history.append({"role": "assistant", "content": answer})
    
    # 5. 保存更新后的对话历史
    save_memory(history)
    
    return answer
if __name__ == "__main__":
    print("=== 带长期记忆的Agent已启动，输入问题开始对话，输入 quit 退出 ===")
    while True:
        user_input = input("你：")
        if user_input.strip().lower() == "quit":
            print("Agent：再见👋")
            break
        answer = chat_with_memory(user_input)
        print(f"Agent：{answer}")