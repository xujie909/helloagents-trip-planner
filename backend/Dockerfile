FROM python:3.12-slim

# 安装 uv（高德MCP依赖）和视频渲染运行时
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    nodejs \
    npm \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

COPY video-generator/package*.json ./video-generator/
RUN cd video-generator && npm install

COPY backend ./backend
COPY video-generator ./video-generator

RUN mkdir -p /data/output /data/audio /data/images

WORKDIR /app/backend

EXPOSE 8000
CMD ["gunicorn", "app.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
