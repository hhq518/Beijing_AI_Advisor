from prompts import BEIJING_REAL_ESTATE_ANALYST, FEW_SHOT_EXAMPLES, CHAIN_OF_THOUGHT_PROMPT, JSON_OUTPUT_PROMPT
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载.env文件中的API Key
load_dotenv()
API_KEY = os.getenv("ALIYUN_API_KEY")

# 初始化阿里云百炼的OpenAI兼容客户端
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def select_prompt(mode="default"):
    """
    根据不同模式返回对应的Prompt模板
    mode可选：
    - default：房产分析师角色模板
    - fewshot：带示例的Few-shot模板
    - cot：思维链模板
    - json：结构化JSON输出模板
    """
    if mode == "fewshot":
        return FEW_SHOT_EXAMPLES
    elif mode == "cot":
        return CHAIN_OF_THOUGHT_PROMPT
    elif mode == "json":
        return JSON_OUTPUT_PROMPT
    else:
        return BEIJING_REAL_ESTATE_ANALYST
    
def get_ai_analysis(topic, prompt_mode="default"):
    """调用阿里云百炼的通义千问模型，获取北京房产分析"""
    # 1. 根据模式选择模板
    base_prompt = select_prompt(mode=prompt_mode)
    
    # 2. 把用户问题拼到模板里
    final_prompt = f"{base_prompt}\n用户问题：{topic}"
    
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": final_prompt}]
    )
    return response.choices[0].message.content
# 主程序入口
if __name__ == "__main__":
    print("🏠 北京房产AI智能分析助手已启动！")
    print("请输入你想分析的北京房产相关问题（如“2025年北京房价走势”）：")
    user_topic = input("👇 ")
    result = get_ai_analysis(user_topic)
    print("\n📊 AI分析结果：")
    print(result)