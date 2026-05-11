# 1. 导入FastAPI框架和依赖
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel  # 用来定义请求数据格式
from typing import Optional, List
import uvicorn
import os
from app_agent_LangChain import main_agent  # 导入你自己的Agent主逻辑

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
@app.post("/chat", response_model=ChatResponse, summary="发送对话消息")
def chat(request: ChatRequest):
    """
    接收用户消息，调用Agent生成回复
    """
    # 调用你自己的Agent主逻辑，传入用户消息和会话ID
    response = main_agent(user_input=request.message, session_id=request.session_id)
    return {
        "response": response,
        "session_id": request.session_id or "default"
    }

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
@app.get("/history", summary="查看对话历史")
def get_history(session_id: Optional[str] = None):
    """
    根据会话ID查询历史对话记录
    """
    # 这里可以连接你的数据库/缓存，返回历史记录，示例代码直接返回空列表
    return {"history": [], "session_id": session_id}

# 启动服务的入口
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app", 
        host="0.0.0.0",  # 允许所有设备访问
        port=8000, 
        reload=True  # 开发模式下自动重载代码修改
    )