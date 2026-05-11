import sqlite3
import os
from datetime import datetime
import chromadb
from chromadb.config import Settings

# ------------------- 1. SQLite 会话存储模块 -------------------
# 作用：用轻量级SQLite数据库保存对话历史，不用额外安装服务
class SessionStorage:
    def __init__(self, db_path="chat_history.db"):
        # 初始化数据库连接
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        # 创建对话历史表（如果不存在）
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,  -- user / assistant
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_message(self, session_id: str, role: str, message: str):
        """添加一条对话记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)",
            (session_id, role, message)
        )
        self.conn.commit()

    def get_recent_messages(self, session_id: str, limit: int = 5):
        """获取最近的N条对话记录"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, message, timestamp FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        return cursor.fetchall()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

# ------------------- 2. ChromaDB 持久化模块 -------------------
# 作用：把向量库数据存到硬盘上，重启程序后数据不丢失
class PersistentChromaDB:
    def __init__(self, persist_dir="./chroma_db"):
        # 持久化配置：数据会保存在 ./chroma_db 目录下
        # 禁用遥测和自动下载模型
        import os
        os.environ["CHROMA_TELEMETRY"] = "false"
        os.environ["CHROMA_AUTO_DOWNLOAD"] = "false"
        
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False,
                persist_directory=persist_dir
            )
        )
        self.collection = self.client.get_or_create_collection(name="property_docs")

    def add_documents(self, documents, metadatas=None, ids=None):
        """添加文档到向量库"""
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query(self, query_text, n_results=3):
        """查询相似文档"""
        return self.collection.query(query_texts=[query_text], n_results=n_results)

    def count(self):
        """获取文档总数"""
        return self.collection.count()

# ------------------- 测试代码 -------------------
if __name__ == "__main__":
    # 1. 先测试SQLite会话存储
    print("=== 测试SQLite会话存储 ===")
    session_store = SessionStorage()
    test_session = "test_session_001"
    
    # 存入3条对话
    session_store.add_message(test_session, "user", "北京朝阳区房价怎么样？")
    session_store.add_message(test_session, "assistant", "朝阳区房价普遍较高，核心区均价在10万/㎡以上...")
    session_store.add_message(test_session, "user", "有没有性价比高的区域？")
    
    # 查询最近5条对话
    print("最近的对话记录：")
    for msg in session_store.get_recent_messages(test_session, limit=5):
        print(f"{msg[0]}: {msg[1]} ({msg[2]})")
    
    session_store.close()

    # 2. 再测试ChromaDB持久化
    print("\n=== 测试ChromaDB持久化 ===")
    db = PersistentChromaDB()
    print(f"当前向量库文档数：{db.count()}")
    
    # 强制添加测试文档
    print("正在添加测试文档到向量库...")
    db.add_documents(
        documents=["朝阳区是北京的经济文化中心，房价较高", "东坝是朝阳区的潜力板块，性价比不错"],
        ids=["doc1", "doc2"]
    )
    print("已添加测试文档到向量库")
    print(f"添加后文档数：{db.count()}")