# 1. 基础镜像：官方 Python 3.11 镜像，现在配置了国内源，能正常拉取
FROM python:3.11

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖清单
COPY requirements.txt .

# 4. 安装依赖（用清华源加速 pip）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 复制项目代码
COPY . .

# 6. 暴露端口
EXPOSE 7860

# 7. 启动命令
CMD ["python", "app_agent_langchain.py"]