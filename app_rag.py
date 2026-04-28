# 1. 导入依赖
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI

# --------------------------
# 2. 初始化配置（从.env文件读取，避免硬编码）
# --------------------------
load_dotenv()  # 加载.env文件里的环境变量
API_KEY = os.getenv("ALIYUN_API_KEY")  # 读取阿里云API密钥

# 初始化通义千问客户端（复用你app.py里的配置）
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# --------------------------
# 3. 加载并处理知识库（RAG核心逻辑）
# --------------------------
def init_knowledge_base():
    """初始化知识库：加载、分块、向量化、存入数据库"""
    print("🔄 正在初始化知识库...")

    # 3.1 加载knowledge.txt文件（用绝对路径，确保不会找不到文件）
    loader = TextLoader(
        r"C:\Users\95381\Desktop\Beijing_AI_Advisor\knowledge.txt",
        encoding="utf-8"
    )
    documents = loader.load()
    print(f"✅ 成功加载知识库，共{len(documents)}个文档")

    # 3.2 文本分块（避免大段文本丢失上下文）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,    # 每个文本块的最大字符数
        chunk_overlap=50,  # 相邻块的重叠字符数，防止断裂
        separators=["\n\n", "\n", "。", "，", " ", ""]
    )
    texts = text_splitter.split_documents(documents)
    print(f"✅ 文本分块完成，共{len(texts)}个文本块")

    # 3.3 初始化嵌入模型（从国内镜像下载，稳定不报错）
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True}
    )

    # 3.4 存入向量数据库（持久化存储，下次不用重新加载）
    db = Chroma.from_documents(
        texts,
        embeddings,
        persist_directory="./chroma_db"  # 数据库文件会存在这个文件夹里
    )
    print("✅ 知识库初始化完成！")
    return db

# --------------------------
# 4. 定义问答函数（RAG检索+Prompt调优+生成回答）
# --------------------------
def rag_answer(question, db):
    """
    带RAG的问答函数
    :param question: 用户输入的问题
    :param db: 向量数据库对象
    :return: 模型生成的回答
    """
    # 4.1 检索和问题最相关的知识库内容
    print("🔍 正在检索相关信息...")
    docs = db.similarity_search(question, k=3)  # 取最相关的3个文本块
    context = "\n\n".join([doc.page_content for doc in docs])  # 拼接检索到的内容

    # 4.2 Prompt调优（核心！强制模型用知识库回答，不编造信息）
    prompt = f"""你是拥有10年北京房产分析经验的专业顾问，擅长结合政策、市场数据给用户精准的购房建议。

### 回答规则：
1. 必须**严格基于下面的参考信息**回答问题，如果参考信息里没有相关内容，请直接说“我暂时没有这部分信息，无法为您解答”，严禁编造任何内容。
2. 回答要简洁专业，优先使用参考信息里的原话或提炼的关键数据。
3. 回答结构清晰，分点列出核心结论，方便用户快速阅读。
4. 结尾可以补充一句温馨提示，比如“如果需要更具体的区域分析，可以告诉我你的预算和需求”。

### 参考信息：
{context}

### 用户问题：
{question}
"""

    # 4.3 调用通义千问生成回答
    print("🤖 正在生成回答...")
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3  # 控制回答的随机性，数值越低越严谨
    )
    return response.choices[0].message.content

# --------------------------
# 5. 启动主程序（用户交互界面）
# --------------------------
if __name__ == "__main__":
    # 初始化知识库（只需要运行一次）
    db = init_knowledge_base()

    # 欢迎语
    print("\n" + "="*50)
    print("🏠 北京房产AI智能分析助手（知识库版）")
    print("="*50)
    print("功能说明：结合本地知识库，为您提供专业的北京房产咨询服务")
    print("使用提示：")
    print("  1. 直接输入问题即可提问")
    print("  2. 输入 'exit' 随时退出程序")
    print("  3. 输入 'clear' 清空当前对话（当前版本暂不支持，后续可扩展）")
    print("="*50 + "\n")

    # 问答循环
    while True:
        # 获取用户输入
        question = input("👉 请输入您的问题：")

        # 处理特殊指令
        if question.lower() == "exit":
            print("👋 感谢使用，程序已退出！")
            break

        # 调用问答函数
        answer = rag_answer(question, db)

        # 输出回答
        print("\n" + "-"*50)
        print(f"📊 AI回答：\n{answer}")
        print("-"*50 + "\n")