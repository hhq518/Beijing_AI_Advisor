FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 7860

CMD ["python", "-m", "streamlit", "run", "app_ui_multi_turn.py", "--server.address", "0.0.0.0", "--server.port", "7860"]
