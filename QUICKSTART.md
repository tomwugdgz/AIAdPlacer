# pDOOH 系统 - 快速开始指南

本指南帮助你在**新电脑**上快速部署和使用 pDOOH 系统。

---

## 方案 A：仅使用客户端库（调用远程 API）

适用场景：你有一台服务器运行 pDOOH 服务端，其他电脑只需要调用 API。

### 步骤

1. **安装 Python 3.8+**
   - 下载：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **安装 pDOOH 客户端库**
   ```bash
   # 方法 1：从本地安装
   git clone https://github.com/你的用户名/AIAdPlacer.git
   cd AIAdPlacer
   pip install -e .

   # 方法 2：从 PyPI 安装（如果已发布）
   pip install pdooh-client
   ```

3. **使用示例**
   ```python
   from pdooh_client import PDOOHClient

   # 连接远程服务器
   client = PDOOHClient(base_url="http://你的服务器IP:5002")

   # 查询智能屏
   screens = client.mcp.query_screens(city="广州", limit=10)

   # 计算 ROI
   roi_result = client.roi.calc_roi(
       frames=1000,
       period_weeks=2,
       category="日化用品"
   )
   ```

---

## 方案 B：使用 Web 管理界面（浏览器操作）

适用场景：你想通过浏览器直观地操作 pDOOH 系统。

### 步骤

1. **下载 Web 界面**
   - 复制 `web/index.html` 到新电脑

2. **打开 Web 界面**
   - 双击 `web/index.html`（会用默认浏览器打开）
   - 或者拖拽到浏览器窗口

3. **配置 API 地址**
   - 点击左侧 "系统设置"
   - 修改 API 地址（默认 `http://47.253.159.62:5002`）
   - 点击 "保存配置"

4. **开始使用**
   - 首页：查看系统状态
   - 点位查询：查询智能屏、门禁、道闸等
   - 投放计划：创建和查询投放计划
   - ROI 计算：计算投资回报率
   - 竞品分析：查看竞品数据

**注意**：如果服务端未启动，Web 界面会使用 Mock 数据演示功能。

---

## 方案 C：部署服务端（完整部署）

适用场景：你想在新电脑上运行完整的 pDOOH 服务端（MCP Server + Tom Agent + ROI Agent + 竞品 Agent）。

### Windows 部署

1. **安装 Python 3.8+**
   - 下载：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **安装 Git（可选）**
   - 下载：https://git-scm.com/download/win

3. **下载 pDOOH 项目**
   ```bash
   git clone https://github.com/你的用户名/AIAdPlacer.git
   cd AIAdPlacer/backend
   ```

4. **运行安装脚本**
   ```bat
   # 右键点击 → 以管理员身份运行
   install.bat
   ```

5. **启动服务**
   ```bat
   start_all.bat
   ```

6. **验证服务**
   - 打开浏览器访问：http://127.0.0.1:5002/health
   - 应该看到：`{"status": "ok", "service": "mcp-server"}`

### Linux/macOS 部署

1. **安装 Python 3.8+**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv

   # macOS
   brew install python3
   ```

2. **下载 pDOOH 项目**
   ```bash
   git clone https://github.com/你的用户名/AIAdPlacer.git
   cd AIAdPlacer/backend
   ```

3. **运行安装脚本**
   ```bash
   chmod +x start_all.sh stop_all.sh
   ./start_all.sh
   ```

### Docker 部署（推荐生产环境）

1. **安装 Docker**
   - Windows：https://docs.docker.com/desktop/install/windows-install/
   - Linux/macOS：https://docs.docker.com/engine/install/

2. **下载 pDOOH 项目**
   ```bash
   git clone https://github.com/你的用户名/AIAdPlacer.git
   cd AIAdPlacer/backend
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f
   ```

5. **停止服务**
   ```bash
   docker-compose down
   ```

---

## 方案 D：开发环境部署

适用场景：你想修改代码或开发新功能。

### 步骤

1. **安装依赖**
   ```bash
   cd d:/Mirofish/AIAdPlacer/backend
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   nano .env  # 按需编辑
   ```

3. **运行服务（开发模式）**
   ```bash
   python run_all_agents.py
   ```

4. **运行客户端库测试**
   ```bash
   cd d:/Mirofish
   pytest pdooh_client/tests/
   ```

---

## 常见问题 (FAQ)

### Q1: 如何修改服务端口？

编辑 `.env` 文件：
```bash
MCP_SERVER_PORT=5002
TOM_AGENT_PORT=5003
ROI_AGENT_PORT=5004
COMPETITOR_AGENT_PORT=5005
```

### Q2: 如何启用 CORS（Web 界面访问）？

编辑 `.env` 文件：
```bash
ENABLE_CORS=true
CORS_ORIGINS=["*"]
```

### Q3: 如何查看日志？

日志文件位置：
- MCP Server：`logs/mcp_server.log`
- Tom Agent：`logs/tom_agent.log`
- ROI Agent：`logs/roi_agent.log`
- 竞品 Agent：`logs/competitor_agent.log`

### Q4: 如何停止服务？

**Windows**：
```bat
stop_all.bat
```

**Linux/macOS**：
```bash
./stop_all.sh
```

**Python 跨平台**：
```bash
python run_all.py --stop
```

### Q5: 如何更新代码？

```bash
cd d:/Mirofish/AIAdPlacer
git pull origin main
cd backend
pip install -r requirements.txt  # 如果有新依赖
```

### Q6: ROI Agent 返回 500 错误怎么办？

检查日志：
```bash
tail -f logs/roi_agent.log
```

常见原因：
1. 参数验证失败（检查请求参数）
2. 数据库连接失败（检查 .env 配置）
3. 外部 API 调用失败（检查网络）

### Q7: 如何在其他电脑上访问服务端？

1. 确保服务端电脑防火墙允许端口 5002-5005
2. 修改 `.env` 文件中的 `HOST=0.0.0.0`
3. 重启服务
4. 在其他电脑上访问：`http://服务端IP:5002`

---

## 文件清单

### Python 客户端库
- `pdooh_client/` - 客户端库源码
- `setup.py` - 安装配置
- `README.md` - 使用文档

### Web 管理界面
- `web/index.html` - 单文件 Web 应用（97KB）

### 服务端打包脚本
- `backend/install.bat` - Windows 安装脚本
- `backend/start_all.bat` - Windows 启动脚本
- `backend/start_all.sh` - Linux/macOS 启动脚本
- `backend/stop_all.sh` - Linux/macOS 停止脚本
- `backend/run_all.py` - Python 跨平台启动脚本
- `backend/Dockerfile` - Docker 镜像定义
- `backend/docker-compose.yml` - Docker Compose 配置

### 优化后的服务端代码
- `backend/app/common.py` - 公共模块
- `backend/app/mcp_server.py` - MCP Server（22个工具）
- `backend/app/roi_agent.py` - ROI Agent（优化版）
- `backend/app/tom_agent.py` - Tom Agent（优化版）
- `backend/app/competitor_agent.py` - 竞品 Agent（优化版）

---

## 技术支持

如有问题，请检查：
1. `docs/OPTIMIZATION-REPORT.md` - 优化报告
2. `backend/README.md` - 服务端文档
3. `pdooh_client/README.md` - 客户端库文档

或者联系开发者：Tom (1980年10月29日生，粤语使用者)

---
**最后更新**：2026-06-19
**版本**：v1.0.0
