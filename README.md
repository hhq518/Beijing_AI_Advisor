# 🏠 Beijing AI Advisor

一个面向北京房地产咨询场景的 AI 应用作品集项目，适合初学者学习与展示。该仓库同时包含一条可运行的、接近生产形态的应用路径，以及多个独立的教学示例，用于展示项目从基础能力到完整应用的演进过程。

## 项目展示能力

- 通过 OpenAI 兼容 API 调用 DashScope / Qwen 聊天补全能力。
- 基于本地 `knowledge.txt` 文件与 ChromaDB 实现 RAG（检索增强生成）。
- 提供 Streamlit Web UI 示例，覆盖单轮对话与多轮对话场景。
- 使用 FastAPI 对 LangChain Agent 进行服务化封装。
- 包含 Function Calling、工具编排、RAG 与输入安全等面向学习和面试讲解的示例。

## 仓库结构

```text
Beijing_AI_Advisor/
├── api_server.py              # FastAPI production API entry point
├── app.py                     # Basic production CLI chat entry point
├── app_agent.py               # Agent implementation example with tools and memory
├── app_agent_LangChain.py     # LangChain Agent used by the API server
├── app_ui_web.py              # Streamlit RAG web UI
├── app_ui_multi_turn.py       # Streamlit multi-turn chat UI
├── database_manager.py        # SQLite session storage and ChromaDB helper classes
├── prompts.py                 # Prompt templates
├── knowledge.txt              # Local Beijing real-estate knowledge base
├── docs/architecture.md       # Architecture notes and diagram
├── images/                    # Project screenshots and presentation assets
├── Dockerfile                 # Streamlit container
├── Dockerfile.api             # FastAPI container
├── docker-compose.yml         # Local container orchestration
├── requirements.txt           # Python dependencies
├── .env.example               # Safe environment variable template
│
├── app_fc.py                  # Educational demo: RAG + Function Calling
├── app_rag.py                 # Educational demo and reusable RAG functions
├── tool_orchestration_demo.py # Educational demo: tool routing/orchestration
└── security_guard.py          # Educational demo: prompt-injection/input guard
```

`chroma_db/`、`chat_history.db`、`agent_sessions.db`、`agent_audit_log.json` 和 `__pycache__/` 等生成文件会在运行时自动创建，不应手动编辑。

## 生产路径

最清晰的生产化应用路径如下：

1. `app_ui_multi_turn.py` 或 `app_ui_web.py` 提供 Streamlit 用户界面。
2. `api_server.py` 通过 FastAPI 暴露 Agent 能力。
3. `app_agent_LangChain.py` 包含 API 服务使用的 LangChain Agent。
4. `database_manager.py` 负责存储聊天历史，并提供向量存储相关辅助类。
5. `knowledge.txt` 与 `app_rag.py` 提供本地 RAG 知识来源和检索函数。

教学示例文件被有意保留，便于学习和面试讲解。它们适合用来说明项目的演进过程，但不是主要的生产部署路径。

## 环境变量

基于示例模板创建本地 `.env` 文件：

```bash
cp .env.example .env
```

随后填写你的 DashScope 凭证：

```env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

不要提交 `.env` 文件。Git 仓库中只应保存 `.env.example`，用于安全地说明所需配置项。

## 本地安装

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

在运行任何 AI 功能之前，请先在 `.env` 中填入真实的 `DASHSCOPE_API_KEY`。

## 运行命令

### 基础 CLI 对话

```bash
python app.py
```

### RAG CLI 示例

```bash
python app_rag.py
```

### Streamlit RAG Web UI

```bash
python -m streamlit run app_ui_web.py --server.address 0.0.0.0 --server.port 7860
```

### Streamlit 多轮对话 Web UI

```bash
python -m streamlit run app_ui_multi_turn.py --server.address 0.0.0.0 --server.port 7860
```

### FastAPI 服务

```bash
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

## Docker 使用

构建并运行 Streamlit UI 容器：

```bash
docker build -t beijing-ai-advisor .
docker run --env-file .env -p 7860:7860 beijing-ai-advisor
```

构建并运行 FastAPI 容器：

```bash
docker build -f Dockerfile.api -t beijing-ai-advisor-api .
docker run --env-file .env -p 8000:8000 beijing-ai-advisor-api
```

使用 Docker Compose 启动：

```bash
docker compose up --build
```

Compose 文件会启动两个服务：

- Streamlit 界面：<http://localhost:7860>
- FastAPI 接口：<http://localhost:8000>

## 截图

![项目演示](images/demo.png)

## 面试讲解要点

- 说明生产路径与教学示例之间的区别。
- 展示 RAG 如何基于 `knowledge.txt` 为回答提供本地知识依据。
- 解释为什么使用 `.env` 保护密钥，以及为什么用 `.env.example` 安全地记录配置项。
- 讲解 `docs/architecture.md` 中的分层架构设计。
- 演示本地启动命令与 Docker 启动命令。
