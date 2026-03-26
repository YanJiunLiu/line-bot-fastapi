# 1. 使用官方 Python 輕量版作為基底
FROM python:3.13-slim

# 2. 設定容器內的工作目錄
WORKDIR /app

# 3. 先複製依賴清單，利用 Docker 快取機制加速構建
COPY requirements.txt .

# 4. 安裝必要的套件
RUN pip install --no-cache-dir -r requirements.txt

# 6. 暴露 FastAPI 運作的連接埠
EXPOSE 8000

# 7. 啟動指令：使用 uvicorn 執行 app
# 這裡假設你的主程式檔名為 main.py，且 FastAPI 實例名為 app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]