# ═══════════════════════════════════════════════════════════
# pDOOH 服务端 Docker 镜像
# ═══════════════════════════════════════════════════════════
# 构建方式:
#   docker build -t pdoh-backend:latest .
#
# 运行方式:
#   docker run -d -p 5002:5002 -p 5003:5003 -p 5004:5004 -p 5005:5005 \
#     --name pdoh-backend \
#     --env-file .env \
#     -v $(pwd)/data:/app/data \
#     pdoh-backend:latest
#
# 或使用 docker-compose:
#   docker-compose up -d
# ═══════════════════════════════════════════════════════════

FROM python:3.13-slim-bookworm

# ── 环境变量 ─────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ── 安装系统依赖 ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── 设置工作目录 ───────────────────────────────────────────────
WORKDIR /app

# ── 复制依赖文件并安装 Python 包 ───────────────────────────
# 先复制 requirements.txt 可以利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ── 复制整个 backend 目录 ───────────────────────────────────
COPY . .

# ── 创建非 root 用户 ────────────────────────────────────────
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# ── 暴露端口 ─────────────────────────────────────────────────
# MCP Server: 5002
# Tom Agent: 5003
# ROI Agent: 5004
# Competitor Agent: 5005
EXPOSE 5002
EXPOSE 5003
EXPOSE 5004
EXPOSE 5005

# ── 健康检查 ────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://127.0.0.1:5002/health')" || exit 1

# ── 启动命令 ──────────────────────────────────────────────────
# 使用 run_all_agents.py 启动所有 Agent
CMD ["python", "run_all_agents.py"]

# ═══════════════════════════════════════════════════════════
# 使用说明
# ═══════════════════════════════════════════════════════════
# 
# 1. 构建镜像:
#    cd backend/
#    docker build -t pdoh-backend:latest .
#
# 2. 运行容器（使用 .env 文件）:
#    docker run -d \
#      -p 5002:5002 -p 5003:5003 -p 5004:5004 -p 5005:5005 \
#      --name pdoh-backend \
#      --env-file .env \
#      -v $(pwd)/data:/app/data \
#      pdoh-backend:latest
#
# 3. 查看日志:
#    docker logs -f pdoh-backend
#
# 4. 停止容器:
#    docker stop pdoh-backend
#
# 5. 使用 docker-compose（推荐）:
#    docker-compose up -d
#    docker-compose logs -f
#    docker-compose down
#
# ═══════════════════════════════════════════════════════════
