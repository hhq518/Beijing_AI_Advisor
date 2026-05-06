from openai import OpenAI
from dotenv import load_dotenv
import os

# 1. 加载环境变量（和你之前的项目逻辑一致，不用额外配置）
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# 2. 多模态分析函数：核心就是构造「带图片的对话消息」
def analyze_house_image(image_url: str):
    """
    传入一张房产图片URL，让AI分析户型并给出建议
    """
    # 这里是多模态的关键：消息不再只是纯文本，而是「文本+图片」的组合
    response = client.chat.completions.create(
        model="qwen-vl-max",  # 通义千问的多模态模型，支持图片解析
        messages=[
            {
                "role": "user",
                "content": [
                    # 第一个元素：文本提问
                    {"type": "text", "text": "帮我分析这张户型图，描述一下户型结构，再结合房产知识给我一个估价和优缺点分析"},
                    # 第二个元素：图片URL，模型会自动解析这张图片
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    )
    return response.choices[0].message.content

# 3. 交互入口
if __name__ == "__main__":
    print("=== 房产户型多模态分析工具 ===")
    # 你可以在这里替换成你的图片URL
    IMAGE_URL = "https://ts1.tc.mm.bing.net/th/id/OIP-C.5GqXukIKNU730bH6T1WTpgHaIK?r=0&rs=1&pid=ImgDetMain&o=7&rm=3"
    print(f"正在分析图片：{IMAGE_URL}")
    result = analyze_house_image(IMAGE_URL)
    print("\n=== AI分析结果 ===")
    print(result)