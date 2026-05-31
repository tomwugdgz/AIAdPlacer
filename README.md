# 🎯 AIAdPlacer — 全球首个 AI 驱动的 pDOOH 智能投放系统

<p align="center">
  <img src="https://img.shields.io/badge/AI-Native-red?style=flat-square" />
  <img src="https://img.shields.io/badge/pDOOH-Programmatic_DOOH-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/LLM+Agent+RAG-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/⚡-FastAPI-green?style=flat-square" />
</p>

<p align="center">
  <strong>第一个将 LLM + Agent + RAG + Workflow + MCP 完整落地的程序化户外广告平台</strong><br/>
  以「人为锚点、点位为触点」重构户外广告投放范式
</p>

<p align="center">
  🌐 在线体验：<a href="http://duckwolf.cn/cps2.html">duckwolf.cn</a> ｜
  📖 技术博客：<a href="http://duckwolf.cn/cps1.html">duckwolf.cn/blog</a> ｜
  💬 联系：<a href="mailto:duckwolf@qq.com">tom@duckwolf.cn</a>
</p>

---

## 🔥 为什么这个项目值得关注？

> **pDOOH（程序化数字户外广告）是全球广告科技的下一个万亿级赛道，但目前尚无一个开源、完整、可落地的 AI Native 系统。**

AIAdPlacer 填补了这个空白：

- ✅ **全球首个** AI Native pDOOH 开源系统
- ✅ 完整实现 **5V 数据模型**（人口 / 消费 / 社区 / 门禁 / 行为）
- ✅ **A2A 接口**（AI-to-AI），其他 AI Agent 可直接调用投放能力
- ✅ 对接**腾讯地图 LBS** + **青柠科技**社区数据底座
- ✅ 内置 **LLM Agent 编排**（人群洞察 → 智能排期 → 动态创意 → 效果归因）

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────┐
│                 前端展示层                        │
│  demo.html（腾讯地图可视化）· bmn-frontend/     │
└──────────────────┬──────────────────────────────┘
                     │ REST / WebSocket
┌─────────────────────────────────────────────────────┐
│                FastAPI 后端层  (Port 5002)          │
│  /api/v2/pdooh/*  ·  /api/v2/agents/*           │
│  /api/v2/rag/*   ·  /api/v2/mcp/*  (A2A)      │
└──────────────────┬──────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│                  AI 能力层                           │
│  LangGraph Agent 编排  ·  ChromaDB 向量检索       │
│  Ollama 本地 LLM (qwen3.5-9B)                  │
└──────────────────┬──────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│                  数据层                              │
│  PostgreSQL (pdooh + ai_adplacer)                │
│  Redis · ChromaDB                                 │
└─────────────────────────────────────────────────────┘
```

---

## 🗃️ 核心数据模型（青柠科技 5V 底座）

| V层 | 数据维度 | 表中字段 | 业务价值 |
|------|----------|----------|----------|
| **V1** 人口属性 | 年龄/性别/学历/收入 | `person_anchor` | 基础人群定向 |
| **V2** 消费偏好 | 母婴/汽车/理财 DMP标签 | `person_dmp_tags` | 精准兴趣投放 |
| **V3** 社区属性 | 楼盘/户型/房价/入住率 | `screen.extended_props` | 社区价值评估 |
| **V4** 门禁动作 ⭐ | 扫码/刷脸/刷卡记录 | `spatial_trajectory` | **独家优势**：真实到店证据 |
| **V5** 线上行为 | APP使用/浏览轨迹 | `person_dmp_tags (extended)` | 跨屏人群扩展 |

> 💡 **V4 门禁数据**是青柠科技的核心壁垒——每次「开门」都是一次真实到店验证，任何其他 pDOOH 系统都不具备这个数据维度。

---

## 🚀 快速启动

### 1️⃣ 克隆项目

```bash
git clone https://github.com/tomwugdgz/AIAdPlacer.git
cd AIAdPlacer
```

### 2️⃣ 准备环境

```bash
# Python 3.13+
cd backend
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 3️⃣ 配置环境变量（`.env`）

```env
# 数据库（需预先创建 pdooh 和 ai_adplacer 两个库）
DATABASE_URL=postgresql://quantdinger:quantdinger123@127.0.0.1:5432/ai_adplacer
PDOOH_DATABASE_URL=postgresql://quantdinger:quantdinger123@127.0.0.1:5432/pdooh

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# 腾讯地图 API
TENCENT_MAP_KEY=7HKBZ-HQBEM-XS56X-6DBAT-ITXUZ-IDFNG

# LLM（Ollama 本地）
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=modelscope.cn/bge-m3:latest
```

### 4️⃣ 初始化数据库

```bash
psql -U quantdinger -d pdooh -f docs/schema.sql
psql -U quantdinger -d ai_adplacer -f docs/ai_ad_schema.sql
```

### 5️⃣ 启动后端

```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```

### 6️⃣ 打开前端 Demo

浏览器访问：`http://127.0.0.1:5002/static/demo.html`

---

## 📡 API 文档

启动后访问 Swagger 自动文档：**http://127.0.0.1:5002/docs**

### pDOOH 核心接口

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v2/pdooh/screens` | 智能屏列表（支持经纬度+半径筛选） |
| GET | `/api/v2/pdooh/screens/{id}/audience` | 单屏受众画像 |
| GET | `/api/v2/pdooh/persons?tags=母婴,亲子` | 人群锚点查询 |
| GET | `/api/v2/pdooh/poi?category=餐饮` | POI 数据点 |
| POST | `/api/v2/pdooh/campaigns` | 创建 AI 投放计划 |
| GET | `/api/v2/pdooh/stats/districts` | 行政区屏量统计 |

### A2A MCP 接口（AI-to-AI）

外部 AI Agent 可通过 MCP 协议调用：

```
tools:
  - search_screens         # 按位置/标签搜索屏
  - get_screen_audience   # 获取屏受众画像
  - create_campaign       # 创建投放计划
  - query_person_tags     # 查询 DMP 标签
  - match_audience_targeting  # AI 人群定向匹配
```

---

## 🎨 前端 Demo 功能

打开 `demo.html` 可以看到：

- 🗺️ **腾讯地图可视化**：智能屏标注 + 热力图（真实数据驱动）
- 📊 **核心指标卡片**：屏总数 / 覆盖行政区 / 日均流量 / POI 数据点 / 人群锚点
- 📋 **行政区统计表格**：按区聚合屏量与人流
- 📍 **智能屏列表**：右侧面板，可投放状态展示
- ➕ **新建投放计划**：弹窗输入，对接真实 API

---

## 🤖 AI Agent 能力

系统内置 4 个专业 Agent（LangGraph 编排）：

| Agent | 功能 | 输入 → 输出 |
|-------|------|------------|
| 🔍 人群洞察 Agent | KMeans 聚类 + DMP 标签分析 | 目标人群描述 → 人群包 |
| 📅 智能排期 Agent | FM + deepMCP 多目标优化 | 预算+时段+屏列表 → 最优排期 |
| 🎨 动态创意 Agent | AIGC + DCO 实时优化 | 产品信息 → 多版创意 |
| 📈 效果归因 Agent | 跨端匹配 + 可信 ID | 投放日志 → 归因报告 |

---

## 📂 项目结构

```
AIAdPlacer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 主入口
│   │   ├── pdooh_api.py       # pDOOH 真实数据 API（9个端点）
│   │   ├── pdooh_mcp.py       # A2A MCP Server 接口
│   │   ├── models.py           # SQLAlchemy 模型
│   │   ├── api/                # v1 传统 REST API
│   │   └── bmn/               # BMN 品牌增长系统
│   └── venv/
├── demo.html                    # 前端 Demo（腾讯地图）
├── docs/
│   ├── schema.sql             # pDOOH 数据库 Schema
│   ├── pdoh_whitepaper_v2.md  # 项目白皮书（含青柠5V论证）
│   └── github_upload_guide.md # GitHub 上传指南
└── README.md
```

---

## 🔬 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.13 · FastAPI · SQLAlchemy · psycopg2 |
| AI | LangGraph · LangChain · Ollama (qwen3.5-9B) · ChromaDB |
| 数据库 | PostgreSQL 16 · Redis 3.0 |
| 前端 | HTML5 · CSS3 · Vanilla JS · 腾讯地图 GL JS API |
| 地图 | 腾讯地图 WebService API（POI / 地理编码 / 路线规划） |
| 部署 | Nginx（反代）· Windows Service（可选） |

---

## 🌟 核心创新点

### 1. 人为锚点（Person Anchor）

以 `TAID` 为唯一标识，绑定 `OAID / MAC / 人脸特征 Hash`，实现跨屏、跨设备、跨时间的唯一用户识别。

```sql
-- 可信 ID 绑定表示例
SELECT taid, oaid, mac_hash, face_feature_hash
FROM trusted_id_binding
WHERE taid = 'TA-2024-00001';
```

### 2. A2A 接口（AI-to-AI）

其他 AI Agent 可通过标准 MCP 协议直接调用投放能力：

```python
# 外部 AI Agent 调用示例
result = mcp_call(
    server="AIAdPlacer",
    tool="create_campaign",
    params={"name": "母婴人群投放", "budget": 50000, ...}
)
```

### 3. 合规优先设计

- AI 生成内容自动标注 `human_visible=false`
- 人脸/MAC 数据全部 Hash 化，不存储原始值
- 完整审计日志 `ai_compliance_log`

---

## 📈 数据库统计（当前入库数据）

| 表名 | 记录数 | 说明 |
|------|--------|------|
| `screen` | 9,801 | 智能屏资产（模拟扩展） |
| `person_anchor` | 500 | 人群锚点 |
| `spatial_trajectory` | 8,979 | 空间轨迹（家-工作-屏） |
| `poi_data` | 13,362 | POI 数据点 |
| `person_dmp_tags` | 10,000 | DMP 标签（55 维） |

---

## 🚧 开发路线图

- [x] **v2.0** pDOOH 数据库设计 + 真实数据 API
- [x] `demo.html` 连接真实数据库
- [x] A2A MCP Server 接口
- [x] 青柠科技 5V 数据模型论证白皮书
- [ ] v2.1 接入真实青柠科技数据（广州试点）
- [ ] v2.2 数字联盟可信 ID SDK 集成
- [ ] v3.0 多城市扩展（深圳/佛山/东莞）

---

## 📞 联系 & 关注

> 🌐 **个人网站**：[duckwolf.cn](http://duckwolf.cn) —— AI 科技 · RWA 研究 · pDOOH 实践
>
> 📖 **技术博客**：[duckwolf.cn/blog](http://duckwolf.cn/blog) —— 持续更新 AIAdPlacer 开发实录
>
> 💬 **商务合作**：tom@duckwolf.cn
>
> 🐙 **GitHub**：[@tomwugdgz](https://github.com/tomwugdgz)

**如果这个项目对你有启发，请 Star ⭐ 支持！**

---

## 📄 License

MIT License —— 自由使用、修改、分发。请保留原作者信息。

---

<p align="center">
  <strong>AIAdPlacer</strong> · 第一个 AI Native pDOOH 系统 · Powered by <a href="http://duckwolf.cn">duckwolf.cn</a>
</p>
