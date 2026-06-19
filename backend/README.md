# pDOOH 服务端

> **AI 原生户外广告投放平台** — 让 AI Agent 能直接调用 pDOOH 投放能力

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 文档](#api-文档)
- [部署指南](#部署指南)
- [常见问题](#常见问题)
- [开发指南](#开发指南)

---

## 项目简介

pDOOH（Programmatic Digital Out-of-Home）是一个 AI 原生户外广告投放平台，提供以下核心能力：

- **MCP Server**（端口 5002）：提供 22 个 MCP 工具，支持 AI Agent 直接调用 pDOOH 投放能力
- **Tom Agent**（端口 5003）：户外广告投放专家 Agent，支持对话式投放方案生成
- **ROI Agent**（端口 5004）：广告投放 ROI 计算专家，支持三场景 ROI 预测
- **竞品监测 Agent**（端口 5005）：竞品情报监测系统

### 技术栈

- **后端框架**: FastAPI + Uvicorn
- **数据库**: SQLite（默认）/ PostgreSQL（可选）
- **向量数据库**: ChromaDB
- **AI 框架**: LangChain / LangGraph
- **LLM 支持**: Ollama（本地）/ OpenAI / Anthropic Claude

---

## 功能特性

### 1. MCP Server（端口 5002）

提供 22 个 MCP 工具，覆盖：

- **核心投放工具**（8 个）：查询屏、获取人群画像、创建投放计划、查询报告等
- **本地资源查询**（3 个）：查询社区智能屏、城市统计、搜索楼盘
- **全量媒体资源查询**（7 个）：门禁、单元门、道闸、LED、电梯框架、智能屏 2025、投影屏
- **城市资源汇总**（2 个）：城市资源统计、全国城市汇总
- **客户查询**（1 个）：客户通讯录查询
- **ROI 计算**（1 个）：三场景 ROI 计算

### 2. Tom Agent（端口 5003）

- 对话式投放方案生成（支持流式响应）
- 自然语言点位查询（自动调用 MCP 工具）
- CPM 追踪与对比
- 自动联动 ROI Agent 计算三场景 ROI

### 3. ROI Agent（端口 5004）

- 三场景 ROI 计算（悲观/中性/乐观）
- 灵敏度分析（单参数变动对 ROI 影响）
- 多方案对比
- 公式说明与参数定义
- 行业 ROI 基准对比

### 4. 竞品监测 Agent（端口 5005）

- 竞品数据库查询
- 竞品定价对比
- 市场情报查询与统计

---

## 快速开始

### 方式一：Windows 一键安装（推荐）

1. **运行安装脚本**:
   ```bat
   # 双击运行，或命令行执行
   install.bat
   ```
   安装脚本会自动：
   - 检查 Python 版本（需要 3.8+）
   - 创建虚拟环境 `venv`
   - 升级 pip
   - 安装依赖（使用清华大学镜像源加速）
   - 创建 `.env` 配置文件
   - 检查数据库文件

2. **编辑配置文件**:
   ```bat
   # 用记事本打开配置文件
   notepad .env
   ```
   最小配置（快速启动）：
   ```env
   DATABASE_URL=sqlite:///./pdooh.db
   DEBUG=true
   LLM_ENABLED=false  # 先禁用 LLM，无需配置大模型
   ```

3. **启动所有 Agent**:
   ```bat
   # 双击运行，或命令行执行
   start_all.bat
   ```
   或直接运行：
   ```bash
   python run_all_agents.py
   ```

4. **访问服务**:
   - MCP Server: http://127.0.0.1:5002/health
   - Tom Agent: http://127.0.0.1:5003/health
   - ROI Agent: http://127.0.0.1:5004/health
   - 竞品监测 Agent: http://127.0.0.1:5005/health

### 方式二：手动安装（Windows / Linux / macOS）

#### 1. 检查 Python 版本

```bash
python --version  # 需要 3.8 或更高版本
```

如果没有 Python，下载安装：https://www.python.org/downloads/

#### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate.bat

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 使用清华大学镜像源（国内推荐）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用默认源
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填入正确的配置值
# Windows:
notepad .env
# Linux / macOS:
nano .env
```

最小配置（快速启动）：
```env
DATABASE_URL=sqlite:///./pdooh.db
DEBUG=true
LLM_ENABLED=false
```

#### 5. 启动服务

```bash
# 启动所有 Agent
python run_all_agents.py
```

---

## 配置说明

### 环境变量（`.env`）

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./pdooh.db` |
| `REDIS_URL` | Redis 连接（可选） | `redis://127.0.0.1:6379/0` |
| `TENCENT_MAP_KEY` | 腾讯地图 API Key（可选） | - |
| `DEBUG` | 调试模式 | `true` |
| `LLM_PROVIDER` | LLM 提供商 | `ollama` |
| `OLLAMA_BASE_URL` | Ollama 服务地址 | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Ollama 模型名称 | `qwen2.5:latest` |
| `LLM_ENABLED` | 是否启用 LLM | `false` |

### 启用 AI 功能（可选）

1. **安装 Ollama**: https://ollama.com/

2. **拉取模型**:
   ```bash
   ollama pull qwen2.5:latest  # 中文友好
   # 或
   ollama pull llama3.1:latest  # 英文友好
   ```

3. **修改 `.env`**:
   ```env
   LLM_ENABLED=true
   OLLAMA_MODEL=qwen2.5:latest
   ```

4. **重启服务**

---

## API 文档

服务启动后，访问自动生成的 API 文档：

- **MCP Server (5002)**: http://127.0.0.1:5002/docs
- **Tom Agent (5003)**: http://127.0.0.1:5003/docs
- **ROI Agent (5004)**: http://127.0.0.1:5004/docs
- **竞品监测 Agent (5005)**: http://127.0.0.1:5005/docs

### 核心 API 端点

#### MCP Server（端口 5002）

- `GET /api/v2/mcp/pdooh/tools/list` — 列出所有可用工具
- `POST /api/v2/mcp/pdooh/tools/call` — 调用工具
- `GET /api/v2/mcp/pdooh/skill.yaml` — 获取 Skill 定义
- `GET /health` — 健康检查

#### Tom Agent（端口 5003）

- `POST /api/v2/tom/chat` — 对话接口（非流式）
- `POST /api/v2/tom/chat/stream` — 对话接口（流式）
- `POST /api/v2/tom/plan/generate` — 投放方案生成
- `GET /health` — 健康检查

#### ROI Agent（端口 5004）

- `POST /api/v2/roi/calculate` — ROI 计算
- `GET /api/v2/roi/three-scenarios` — 三场景 ROI
- `POST /api/v2/roi/sensitivity` — 灵敏度分析
- `GET /api/v2/roi/formula` — 公式说明
- `GET /health` — 健康检查

#### 竞品监测 Agent（端口 5005）

- `GET /api/competitors` — 查询竞品
- `GET /api/pricing` — 竞品定价对比
- `GET /api/intelligence` — 市场情报
- `GET /health` — 健康检查

---

## 部署指南

### 方式一：Docker 部署（推荐生产环境）

1. **构建镜像**:
   ```bash
   docker build -t pdoh-backend:latest .
   ```

2. **使用 docker-compose 启动**:
   ```bash
   docker-compose up -d
   ```

3. **查看日志**:
   ```bash
   docker-compose logs -f
   ```

4. **停止服务**:
   ```bash
   docker-compose down
   ```

### 方式二：传统部署（Linux 服务器）

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **使用 systemd 管理服务**（示例）:
   ```ini
   # /etc/systemd/system/pdooh.service
   [Unit]
   Description=pDOOH Backend Service
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/backend
   Environment="PATH=/path/to/backend/venv/bin"
   ExecStart=/path/to/backend/venv/bin/python run_all_agents.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **启动服务**:
   ```bash
   sudo systemctl enable pdoh
   sudo systemctl start pdoh
   sudo systemctl status pdoh
   ```

---

## 常见问题

### 1. Python 版本过低

**错误**: `Python 3.8 or higher is required`

**解决**: 升级 Python 到 3.8 或更高版本

### 2. 端口被占用

**错误**: `Port 5002 is already in use`

**解决**:
- 修改 `.env` 中的端口配置
- 或停止占用端口的进程

### 3. 数据库文件不存在

**警告**: `数据库未找到`

**解决**: 将以下数据库文件放到 `backend/` 目录：
- `亲邻单元门智能框架.db`
- `亲邻门禁全国点位.db`
- `亲邻广州道闸.db`
- `亲邻商场LED.db`

### 4. LLM 调用失败

**错误**: `LLM 调用失败`

**解决**:
- 检查 `LLM_ENABLED` 是否为 `true`
- 检查 Ollama 是否运行：`ollama list`
- 或设置 `LLM_ENABLED=false` 禁用 LLM（使用规则降级方案）

### 5. 依赖安装失败

**错误**: `pip install` 失败

**解决**:
- 使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 或逐个安装依赖包

---

## 开发指南

### 项目结构

```
backend/
├── app/
│   ├── pdooh_mcp.py        # MCP Server（端口 5002）
│   ├── tom_agent.py         # Tom Agent（端口 5003）
│   ├── roi_agent.py         # ROI Agent（端口 5004）
│   ├── common.py           # 公共模块（日志、错误处理、缓存等）
│   ├── agents/            # Agent 实现
│   ├── api/               # API 路由
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   └── ...
├── competitor_agent.py     # 竞品监测 Agent（端口 5005）
├── run_all_agents.py      # 一键启动所有 Agent
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── install.bat           # Windows 安装脚本
├── start_all.bat         # Windows 启动脚本
├── Dockerfile            # Docker 镜像定义
└── docker-compose.yml   # Docker Compose 配置
```

### 添加新 Agent

1. 在 `app/` 目录创建新的 Agent 模块
2. 在 `run_all_agents.py` 中添加启动逻辑
3. 更新 `.env.example` 添加端口配置
4. 更新 `README.md` 添加 API 文档

### 运行测试

```bash
# 安装测试依赖
pip install pytest httpx

# 运行测试
pytest tests/
```

---

## 许可证

[MIT License](LICENSE)

---

## 联系方式

- **技术支持**: Tom (17665188615)
- **项目文档**: http://127.0.0.1:5002/docs

---

## 更新日志

### v2.1.0 (2026-06-17)

- ✨ 新增 14 个 MCP 工具（共 22 个）
- ✨ 新增竞品监测 Agent（端口 5005）
- ✨ 支持查询六类媒体资源数据
- 🐛 修复若干已知问题

### v2.0.0 (2026-06-01)

- ✨ 初始版本发布
- ✨ 实现 MCP Server + Tom Agent + ROI Agent
- ✨ 支持 Ollama / OpenAI / Anthropic Claude

---

**⭐ 如果本项目对您有帮助，请给我们一个星标！**
