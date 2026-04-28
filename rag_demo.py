import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter# 题目要求重点标注的对象：递归字符文本分割器
from langchain_huggingface import HuggingFaceEmbeddings # 题目要求重点标注的对象：HuggingFace文本向量化模型
from langchain_chroma import Chroma # 题目要求重点标注的对象：Chroma向量数据库
from openai import OpenAI

# ------------------- 1. 加载配置和知识库 -------------------
load_dotenv() # 加载.env文件中的环境变量
API_KEY = os.getenv("ALIYUN_API_KEY")# 从环境变量中读取阿里云API密钥
# 初始化阿里云客户端
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 加载并处理知识库
loader = TextLoader(r"C:\Users\95381\Desktop\Beijing_AI_Advisor\knowledge.txt", encoding="utf-8")
documents = loader.load()# 加载knowledge.txt文件内容
# 2. 文本分块（Chunking）
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100, # 每个文本块的最大字符数
    chunk_overlap=20 # 相邻文本块的重叠字符数，避免信息断裂
)
texts = text_splitter.split_documents(documents) # 把长文档切成多个短文本块

# 3. 文本向量化+存入向量数据库
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"trust_remote_code": True},
    encode_kwargs={"normalize_embeddings": True}
)
db = Chroma.from_documents(texts, embeddings, persist_directory="./chroma_db") # 把文本块向量化后存入Chroma数据库
retriever = db.as_retriever(search_kwargs={"k": 2})# 创建检索器，每次返回最相似的2个文本块

# ------------------- 2. 手动实现RAG问答 -------------------
# 题目要求重点标注的对象：similarity_search（相似性检索）
# 下面的rag_answer函数里会用到这个方法
def rag_answer(question):
    # 步骤1：从知识库中检索相关内容 问题向量化 + 相似性检索
    docs = retriever.invoke(question)
    context = "\n".join([doc.page_content for doc in docs])

    # 步骤2：把问题+上下文发给大模型 构建增强Prompt
    prompt = f"""你是专业的北京房产分析师，请根据下面的参考信息回答用户问题，回答要简洁专业：
参考信息：
{context}

用户问题：{question}
"""
    # 步骤3：调用大模型生成回答
    response = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ------------------- 3. 启动问答 -------------------
if __name__ == "__main__":
    print("🏠 北京房产RAG问答助手启动！")
    print("输入问题提问，输入exit退出")
    while True:
        q = input("\n👉 请输入问题：")
        if q.lower() == "exit":
            print("👋 退出程序")
            break
        ans = rag_answer(q)
        print(f"\n📊 AI回答：{ans}")