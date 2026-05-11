# 1. 导入FastAPI框架和依赖
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel  # 用来定义请求数据格式
from typing import Optional, List
import uvicorn
import os
from app_agent_LangChain import main_agent  # 导入你自己的Agent主逻辑
from database_manager import SessionStorage
session_store = SessionStorage()

# 2. 创建FastAPI应用实例
app = FastAPI(
    title="北京房产AI顾问API",
    description="LangChain Agent的RESTful API接口，支持对话、图片分析和历史记录查询",
    version="1.0.0"
)


# 3. 定义请求数据格式（别人调用时，必须按这个格式传数据）
class ChatRequest(BaseModel):
    message: str  # 用户输入的消息
    session_id: Optional[str] = None  # 可选参数：对话会话ID，用来区分不同用户

# 4. 定义响应数据格式（你的接口返回的数据格式）
class ChatResponse(BaseModel):
    response: str  # Agent的回复
    session_id: str  # 会话ID，用于后续对话保持上下文

# ------------------- 接口端点（Endpoint）定义 -------------------

# 健康检查接口：用来验证API是否正常运行
@app.get("/health", summary="健康检查")
def health_check():
    return {"status": "ok", "service": "北京房产AI顾问"}

# 对话接口：核心接口，调用你的Agent进行对话
@app.post("/chat")
async def chat(user_input: str, session_id: str = "default"):
    # 关键步骤1：先把用户输入存进数据库
    session_store.add_message(session_id, "user", user_input)

    # 关键步骤2：调用你的Agent获取回复（这里是你原来的逻辑）
    response = main_agent(user_input)

    # 关键步骤3：把AI回复也存进数据库
    session_store.add_message(session_id, "assistant", response)

    return {"response": response}
# 图片分析接口（可选，如果你有图片分析功能）
@app.post("/analyze-image", summary="分析图片内容")
async def analyze_image(file: UploadFile = File(...)):
    """
    上传图片，调用Agent的多模态分析能力
    """
    # 保存图片到临时文件
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    # 调用Agent的图片分析逻辑（这里用示例代码，你可以替换成自己的多模态逻辑）
    # response = multimodal_agent(image_path=temp_path)
    response = "图片分析功能已接收，正在处理..."
    
    # 删除临时文件
    os.remove(temp_path)
    return {"response": response}

# 对话历史查询接口（可选，用来查看历史对话）
@app.get("/history")
async def get_history(session_id: str = "default", limit: int = 5):
    history = session_store.get_recent_messages(session_id, limit=limit)
    return {
        "session_id": session_id,
        "history": [{"role": msg[0], "message": msg[1], "time": msg[2]} for msg in history]
    }

# 启动服务的入口
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app", 
        host="0.0.0.0",  # 允许所有设备访问
        port=8000, 
        reload=True  # 开发模式下自动重载代码修改
    )