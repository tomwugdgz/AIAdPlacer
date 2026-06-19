# 🎯 AIAdPlacer — 户外广告行业的AI Copilot工具箱

核心价值：
- 帮广告主做投放决策（AI分析+推荐）
- 帮媒体主管理库存（AI排期+定价）
- 帮代理商提升效率（AI报告+竞品监控）

落地路径：
v1 → 成为Tom的私人工具（不求商业化，先验证）
v2 → 卖给3-5个小广告主（测试付费意愿）
v3 → 做成SaaS平台（按投放金额收费）

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
  📖 技术博客：<a href="http://duckwolf.cn/cps1.html">duckwolf.cn/mcp.html</a> ｜
  💬 联系：<a href="mailto:duckwolf@qq.com">tom@duckwolf.cn</a>
</p>

<p align="center">
  📋 接口解说：<a href="http://duckwolf.cn/pd.html">duckwolf.cn/pd.html</a> ｜
  🔗 对接文档：<a href="http://47.253.159.62:5002/docs">http://47.253.159.62:5002/docs</a>
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
- ✅ **符合 T/CCSA 738—2025 行业标准**（程序化户外广告投放曝光测量技术要求）

> 📋 **行业标准对齐**：系统曝光测量逻辑已对标中国广告协会 + 中国通信标准化协会联合发布的行业标准，涵盖流动曝光、驻留曝光、曝光乘数、OTC 概率等核心指标。详见 [`docs/industry_standard_terms_and_guide.md`](docs/industry_standard_terms_and_guide.md)

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────┐
│                 前端展示层                        │
│  demo.html（腾讯地图可视化）· bmn-frontend/     │
│  bus-demo.html（公交线路热力图）                │
└──────────────────┬──────────────────────────────┘
                     │ REST / WebSocket
┌─────────────────────────────────────────────────────┐
│                FastAPI 后端层  (Port 5002)          │
│  /api/v2/pdooh/*  ·  /api/v2/agents/*           │
│  /api/v2/rag/*   ·  /api/v2/mcp/*  (A2A)      │
│  /api/v2/bus/*    ·  /api/v2/bus-bidding/*    │
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
TENCENT_MAP_KEY=8HKBZ-HQBEM-XS56X-6DBAT-ITXUZ-IDFNG

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

### bus-pDOOH 子系统（公交线路 programmatic 投放）⭐ 新增

针对公交车身广告的独立竞价投放模块：

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v2/bus/routes/import` | Excel 批量导入线路（29城/95线路） |
| GET | `/api/v2/bus/routes` | 线路列表（城市/等级/价格/热力筛选） |
| GET | `/api/v2/bus/routes/{id}` | 线路详情 |
| POST | `/api/v2/bus/bidding/calculate` | 竞价计算（等级系数 + 时段溢价） |
| POST | `/api/v2/bus/bidding/multi` | 多线路组合竞价 |
| POST | `/api/v2/bus/campaigns` | 创建投放方案 |
| POST | `/api/v2/bus/campaigns/{id}/submit-review` | 提交 AI审核 |
| POST | `/api/v2/bus/campaigns/{id}/attribution` | 效果归因报告 |
| GET | `/api/v2/bus/recommend` | 智能线路推荐 |

演示页面：`backend/bus-demo.html`（线路热力地图 + 竞价计算器 + AI审核模拟）

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

### AI 优化接口（v2.0.1）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v2/optimization/scheduling/generate?budget=50000&days=14` | AI 排期优化 |
| GET | `/api/v2/optimization/scheduling/optimize?campaign_id=xxx` | 基于历史数据优化 |
| GET | `/api/v2/optimization/competitor/report?competitor_name=竞对A` | 竞品监控报告 |
| GET | `/api/v2/optimization/competitor/compare?names=竞对A,竞对B` | 竞品对比分析 |
| GET | `/api/v2/dashboard/overview` | 效果归因看板总览 |
| GET | `/api/v2/dashboard/media-performance` | 媒体表现排行 |
| GET | `/api/v2/dashboard/timeline?days=14` | 时间线表现 |
| GET | `/api/v2/dashboard/funnel` | 转化漏斗 |

### 鉴权说明

所有 v2 API 支持两种鉴权模式：

- **API Key**：请求头 `X-API-Key: aiad-2025-placer-token`
- **Bearer Token**：请求头 `Authorization: Bearer aiad-2025-placer-token`

### A2A / MCP 调用指南（AI-to-AI）

> 📖 **完整接口文档**：`http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml`

#### 📌 接口基础信息

| 项目 | 值 |
|------|------|
| Base URL | `http://47.253.159.62:5002` |
| MCP Endpoint | `/api/v2/mcp/pdooh/tools/call` |
| Skill YAML | `/api/v2/mcp/pdooh/skill.yaml` |
| Agent API | `/api/v2/agents/execute` |
| API 文档 | `http://47.253.159.62:5002/docs` |

#### 🔧 获取可用工具列表

```bash
GET /api/v2/mcp/pdooh/tools/list
```

#### 📞 工具调用示例

**1. 查询智能屏点位**
```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_query_screens",
    "arguments": { "city": "广州", "district": "天河区", "min_house_price": 8, "limit": 10 }
  }'
```

**2. 创建投放计划**
```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_create_campaign",
    "arguments": {
      "name": "高端白酒-天河城-周投",
      "screen_ids": [1, 2, 3],
      "start_date": "2026-06-10", "end_date": "2026-06-16",
      "budget": 30000, "creative_type": "image"
    }
  }'
```

**3. 人群洞察分析**
```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_audience_insight",
    "arguments": { "target_city": "广州", "product_desc": "高端白酒，目标高净值人群", "budget_hint": 50000 }
  }'
```

**4. 合规审核**
```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_compliance_check",
    "arguments": { "content": "治愈你的失眠", "industry": "医疗" }
  }'
```

#### 🤖 Agent 任务编排 (A2A)

```bash
curl -X POST http://47.253.159.62:5002/api/v2/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "帮我在广州天河区投放高端白酒广告，预算50万，投放14天",
    "agent": "audience"
  }'
```

#### 🐍 Python SDK

```python
import requests

BASE_URL = "http://47.253.159.62:5002"

def query_screens(city, district, limit=10):
    resp = requests.post(f"{BASE_URL}/api/v2/mcp/pdooh/tools/call", json={
        "name": "pdooh_query_screens",
        "arguments": {"city": city, "district": district, "limit": limit}
    })
    return resp.json()

def create_campaign(name, screen_ids, budget, start_date, end_date):
    resp = requests.post(f"{BASE_URL}/api/v2/mcp/pdooh/tools/call", json={
        "name": "pdooh_create_campaign",
        "arguments": {"name": name, "screen_ids": screen_ids, "budget": budget,
                       "start_date": start_date, "end_date": end_date}
    })
    return resp.json()

# 使用
screens = query_screens("广州", "天河区")
campaign = create_campaign("高端白酒-天河城-周投", [1, 2, 3], 30000, "2026-06-10", "2026-06-16")
```

#### 🔌 Skill YAML

供 AI Agent 加载的配置（`GET /api/v2/mcp/pdooh/skill.yaml`）：

```yaml
name: pdooh-agent
description: pDOOH AI原生投放平台 Skill，让 AI Agent 能直接调用 pDOOH 投放能力。
triggers: ["pDOOH", "户外广告投放", "社区屏", "程序化户外", "投放计划"]
tools:
  - pdooh_query_screens
  - pdooh_get_screen_audience
  - pdooh_create_campaign
  - pdooh_query_campaigns
  - pdooh_submit_creative
  - pdooh_query_report
  - pdooh_compliance_check
  - pdooh_audience_insight
mcp_endpoint: "/api/v2/mcp/pdooh/tools/call"
```

#### 💚 健康检查

```bash
curl http://47.253.159.62:5002/api/v2/mcp/pdooh/health
# {"service": "pDOOH A2A MCP Server", "status": "ok", "tools_count": 16, ...}
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

## 🧠 AI Agents

系统内置 **4 个专业 Agent**，由 LangGraph 编排协同工作：

```mermaid
graph LR
    U[用户输入] --> IA[🔍 人群洞察 Agent]
    IA --> SA[📅 智能排期 Agent]
    SA --> CA[🎨 动态创意 Agent]
    CA --> AA[📈 效果归因 Agent]
    AA --> R[投放结果]
    
    IA -.-> DB[(知识库 / RAG)]
    SA -.-> DB
    CA -.-> DB
    AA -.-> DB
```

| Agent | 功能 | 核心技术 | 输入 → 输出 |
|-------|------|---------|-------------|
| 🔍 **人群洞察 Agent** | KMeans 聚类 + DMP 标签分析 | scikit-learn + LLM | 目标人群描述 → 人群包 |
| 📅 **智能排期 Agent** | 多目标优化排期 | 四维评分 + 贪心算法 | 预算+时段+屏列表 → 最优排期 |
| 🎨 **动态创意 Agent** | AIGC + DCO 实时优化 | LLM 生成 | 产品信息 → 多版创意 |
| 📈 **效果归因 Agent** | 跨端匹配 + OneID | OTC 模型 + 多触点归因 | 投放日志 → 归因报告 |

### AI 排期优化算法

```
Score(screen) = w₁ × traffic_score + w₂ × price_ratio + w₃ × audience_match + w₄ × district_bonus

权重配置（目标可调）:
  optimize_reach:     {traffic: 0.40, price: 0.25, audience: 0.20, district: 0.15}
  optimize_frequency: {traffic: 0.20, price: 0.30, audience: 0.30, district: 0.20}  
  balance (默认):     {traffic: 0.30, price: 0.25, audience: 0.25, district: 0.20}
```

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
│   │   ├── bus/                # ⭐ bus-pDOOH 子系统
│   │   │   ├── models.py       # 5个ORM模型（Routes/Campaigns/Attribution...）
│   │   │   ├── schemas.py      # Pydantic 请求/响应模型
│   │   │   ├── api.py          # 16个REST端点
│   │   │   └── services/       # 竞价引擎/热力评分/AI审核/归因
│   │   ├── services/
│   │   │   └── ollama_client.py # Ollama HTTP 客户端
│   │   ├── api/                # v1 传统 REST API
│   │   └── bmn/               # BMN 品牌增长系统
|   ├── bus-demo.html           # ⭐ bus-pDOOH 演示页面
│   ├── optimization-demo.html  # ⭐ AI 优化模块演示页（排期/竞品/看板）
│   └── venv/
├── demo.html                    # 前端 Demo（腾讯地图）
├── docs/
│   ├── schema.sql             # pDOOH 数据库 Schema
│   ├── bus-pdooh-prd.md       # ⭐ bus-pDOOH 产品需求文档
│   ├── bus-pdooh-system-design.md # ⭐ bus-pDOOH 系统设计
│   ├── pdoh_whitepaper_v2.md  # 项目白皮书（含青柠5V论证）
│   ├── industry_standard_terms_and_guide.md # ⭐ 行业标准术语表+应用指南（T/CCSA 738-2025）
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

### 1. OneID — 跨平台唯一受众 ID ⭐ 新增

以**手机客户信息**为基础，通过 **AI 算法模型**（设备指纹 + AI 匹配）为每个受众生成唯一 ID：

```
手机客户信息 → AI 匹配算法 → OneID（跨 App 打通）
```

**核心价值**：
- 跨 App 平台打通，针对每个 ID 的**二次运营**
- 基于 OneID **实时行为数据**，AI 优化算法**动态调整投放策略**
- 实现从"投屏"到"投人"的范式转变

```sql
-- OneID 示例
SELECT oneid, device_fingerprint, app_ids, last_active, behavior_tags
FROM oneid_registry
WHERE oneid = 'OI-2024-00001';
```

### 2. 一页式投放漏斗（Funnel-on-Grid）

**500 米网格**为单位，将投放全流程浓缩为一张热力图：

```
选点（POI交叉比对） → 出价（OTC模型） → 投放（AI优化） → 归因（OneID追踪）
```

**网格热力系统**：
- **粒度**：500 米 × 500 米雷利网格（Rayleigh Grid）
- **POI 交叉比对**：高德地图 + 腾讯地图双平台验证
- **热力评分**：综合人口密度、消费力、POI 丰富度、竞品分布

### 3. OTC 模型（Opportunity To Contact）

```
OTC = PV × Reach × Frequency × 有效接触系数
```

**约束**：PV 数据作为**上限约束**，Reach & Frequency 不能超过 PV

| 参数 | 说明 | 来源 |
|------|------|------|
| PV | 页面浏览量（上限） | 腾讯地图/高德地图 API |
| Reach | 触达人数 | OneID 去重统计 |
| Frequency | 触达频次 | 500米网格曝光计数 |
| 有效接触系数 | 广告有效触达比例 | AI 模型估算（0.3-0.8） |

### 4. A2A 接口（AI-to-AI）

其他 AI Agent 可通过标准 MCP 协议直接调用投放能力：

```python
# 外部 AI Agent 调用示例
result = mcp_call(
    server="AIAdPlacer",
    tool="create_campaign",
    params={"name": "母婴人群投放", "budget": 50000, ...}
)
```

### 5. 合规优先设计

- AI 生成内容自动标注 `human_visible=false`
- 人脸/MAC 数据全部 Hash 化，不存储原始值
- 完整审计日志 `ai_compliance_log`

---

## 📈 数据库统计（当前入库数据）

### PostgreSQL（主库）

| 表名 | 记录数 | 说明 |
|------|--------|------|
| `screen` | 9,801 | 智能屏资产（模拟扩展） |
| `person_anchor` | 500 | 人群锚点 |
| `spatial_trajectory` | 8,979 | 空间轨迹（家-工作-屏） |
| `poi_data` | 13,362 | POI 数据点 |
| `person_dmp_tags` | 10,000 | DMP 标签（55 维） |

### qinlin_local.db（完整媒体资源库，100,000+ 条）

| 表名 | 记录数 | 说明 |
|------|--------|------|
| 道闸点位 | **1,021** | 社区/商业园区道闸广告位 |
| 单元门点位 | **8,114** | 住宅单元门框架广告位 |
| 门禁点位 | **66,308** | ⭐ 社区门禁终端（独家 V4 数据） |
| 智能屏 L9 | 待接入 | 梯内智能屏 L9 型号 |
| 客户通讯录 | 内部数据 | 客户关系管理数据 |

---

## 🚧 开发路线图

- [x] **v2.0** pDOOH 数据库设计 + 真实数据 API
- [x] `demo.html` 连接真实数据库
- [x] A2A MCP Server 接口
- [x] 青柠科技 5V 数据模型论证白皮书
- [x] **⭐ bus-pDOOH 子系统**完整实现（线路管理/竞价引擎/AI审核/效果归因/演示页）
- [x] **⭐ 行业标准对齐**（T/CCSA 738-2025 曝光测量术语表+应用指南）
- [ ] v2.1 行业标准曝光计算引擎（流动/驻留曝光 + SOT + 曝光乘数 + 接触频次）
- [ ] v2.1 接入真实青柠科技数据（广州试点）
- [ ] v2.2 数字联盟可信 ID SDK 集成
- [ ] v2.3 迪杰斯特拉路径优化 + 运营商数据接入
- [ ] v3.0 多城市扩展（深圳/佛山/东莞）+ 地铁/机场场域模型

### 🖥️ AI pDOOH 云服务（运行中）

| 项目 | 值 |
|------|------|
| 地址 | `http://47.253.159.62:5002` |
| 协议 | REST + MCP (A2A) |
| 状态 | ✅ 运行中 |

#### 🔌 A2A / MCP 接口清单

| 接口 | 地址 | 说明 |
|------|------|------|
| MCP Health | `http://47.253.159.62:5002/api/v2/mcp/pdooh/health` | 健康检查 |
| MCP Tools List | `http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/list` | 列出 16 个工具 |
| MCP Tool Call | `http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call` | 调用具体工具 |
| Skill YAML | `http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml` | SKILL 配置（供 AI Agent 读取） |
| Agent Execute | `http://47.253.159.62:5002/api/v2/agents/execute` | A2A 任务编排 |
| API 文档 | `http://47.253.159.62:5002/docs` | Swagger UI |

#### 🛠️ 16 个 MCP Tools（全部在线 ✅）

> 服务：**pDOOH A2A MCP Server** · 工具总数：**19 个** · 健康检查：✅ OK · 数据库：`qinlin_local.db`（完整版）· 总数据量：**100,000+ 条**

**✅ 核心投放工具（8个）**

| # | 工具名 | 功能 | 状态 |
|---|--------|------|------|
| 1 | `pdooh_query_screens` | 查询智能屏点位 | ✅ |
| 2 | `pdooh_get_screen_audience` | 获取人群画像 | ✅ |
| 3 | `pdooh_create_campaign` | 创建投放计划 | ✅ |
| 4 | `pdooh_query_campaigns` | 查询投放计划 | ✅ |
| 5 | `pdooh_submit_creative` | 提交创意物料 | ✅ |
| 6 | `pdooh_query_report` | 查询效果报告 | ✅ |
| 7 | `pdooh_compliance_check` | 合规审核 | ✅ |
| 8 | `pdooh_audience_insight` | 人群洞察分析 | ✅ |

**✅ 媒体资源查询工具（8个）**

| # | 工具名 | 功能 | 数据来源 | 状态 |
|---|--------|------|----------|------|
| 9 | `pdooh_query_daocha_points` | 道闸点位查询 | 道闸点位（1,021条） | ✅ |
| 10 | `pdooh_query_smart_frames` | 单元门点位查询 | 单元门点位（8,114条） | ✅ |
| 11 | `pdooh_query_access_points` | 门禁点位查询 | 门禁点位（66,308条） | ✅ |
| 12 | `pdooh_query_led_points` | LED 广告屏查询 | 待接入数据 | ✅ |
| 13 | `pdooh_query_elevator_frames` | 电梯框架查询 | 待接入数据 | ✅ |
| 14 | `pdooh_query_shadow_points` | 投影点位查询 | 待接入数据 | ✅ |
| 15 | `pdooh_query_city_resources` | 城市综合资源统计 | 综合统计 | ✅ |
| 16 | `pdooh_query_city_summary` | 城市媒体汇总 | 城市汇总 | ✅ |

#### 📋 SKILL 调用示例

任何 AI Agent 可通过以下方式调用本系统：

```yaml
# 1. 读取 SKILL 配置
GET http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml

# 2. 调用具体工具
POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call
Content-Type: application/json

{
  "tool": "pdooh_create_campaign",
  "params": {
    "name": "母婴人群投放",
    "budget": 50000,
    "audience_tags": ["母婴", "亲子"],
    "days": 14
  }
}
```

**触发词**：`pDOOH`、`户外广告投放`、`社区屏`、`投放计划` 等

#### 🎮 云服务器管理命令

```bash
# 启动服务
/home/admin/.copaw/workspaces/default/start_pdooh.sh start

# 停止服务
/home/admin/.copaw/workspaces/default/start_pdooh.sh stop

# 查看状态
/home/admin/.copaw/workspaces/default/start_pdooh.sh status

# 重启服务
/home/admin/.copaw/workspaces/default/start_pdooh.sh restart
```

#### 🧪 测试命令

```bash
# 健康检查
curl http://47.253.159.62:5002/api/health

# 品牌查询
curl -X POST http://47.253.159.62:8899/v1/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pdooh-agent-key-2026" \
  -d '{"brand":"农夫山泉"}'

# 智能定价
curl -X POST http://47.253.159.62:8899/v1/quote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pdooh-agent-key-2026" \
  -d '{"brand":"元气森林","media":"广告门","city":"广州"}'
```

---

## 📞 联系 & 关注

> 🌐 **个人网站**：[duckwolf.cn](http://duckwolf.cn) —— AI 科技 · RWA 研究 · pDOOH 实践
>
> 📖 **技术博客**：[duckwolf.cn/blog](http://duckwolf.cn) —— 持续更新 AIAdPlacer 开发实录
>
> 💬 **商务合作**：duckwolf@qq.com
>
> 🐙 **GitHub**：[@tomwugdgz](https://github.com/tomwugdgz)

**如果这个项目对你有启发，请 Star ⭐ 支持！**

---

> ### ⚠️ 免责声明
> 
> 本项目所有语料、数据库及资源均来源于公开渠道或模拟生成，仅供技术研究与学习交流使用。
> 如因数据使用涉及侵权问题，请及时联系作者处理。**本软件并非用于商业用途。**
> 
> 📧 联系方式：[tom@duckwolf.cn](mailto:duckwolf@qq.com)

---

## 📸 界面截图

### 🎛️ 控制面板（Dashboard）
![控制面板]<img width="2450" height="1113" alt="ScreenShot_2026-06-19_225619_151" src="https://github.com/user-attachments/assets/13a7f1dc-cf52-4b65-899d-8a36ebd2480c" />



*实时数据概览：点位统计、曝光量、点击率、活跃计划*

### 🔍 点位查询（Point Search）
![点位查询]<img width="2493" height="1245" alt="ScreenShot_2026-06-19_224855_063" src="https://github.com/user-attachments/assets/64b656c0-cd7d-4499-bf39-5b372b6fde48" />


*智能筛选：城市/区域/媒体类型/价格区间*

### 📅 投放计划（Ad Plans）
![投放计划]<img width="2064" height="684" alt="ScreenShot_2026-06-19_225516_249" src="https://github.com/user-attachments/assets/4758432f-ab62-4c16-80a7-09639dcfa31c" />


*计划管理：创建/编辑/暂停/结束，AI 优化建议*

### 📊 ROI 计算器（ROI Calculator）
![ROI 计算器]<img width="2481" height="1215" alt="ScreenShot_2026-06-19_224924_084" src="https://github.com/user-attachments/assets/c9e825b1-3c2a-478f-b191-0e2db126f99b" />


*智能预算分配：UV/PV/转化率/LTV/ROI 一键计算*

### 🏆 竞品分析（Competitor Analysis）
![竞品分析]<img width="1779" height="1026" alt="ScreenShot_2026-06-19_224941_885" src="https://github.com/user-attachments/assets/f4738cd8-ed21-44c6-9a0e-a2e4ef322a81" />


*市场洞察：份额对比/策略分析/趋势预测*

### ⚙️ 系统设置（Settings）
![系统设置]!<img width="1725" height="1131" alt="ScreenShot_2026-06-19_225011_780" src="https://github.com/user-attachments/assets/e4aa3f52-45a2-4130-aa43-fb3a5e23a782" />



*配置管理：API Key/Token/数据库/缓存*

---

## 🌐 在线演示

### 🎮 Web 管理界面
- **本地演示**：打开 `web/index.html`（零依赖，双击即用）
- **在线体验**：[http://duckwolf.cn/cps2.html](http://duckwolf.cn/cps2.html)
- **界面预览**：[http://47.253.159.62:8888](http://47.253.159.62:8888)（Nginx 代理）

### 📖 API 文档
- **Swagger UI**：[http://47.253.159.62:5002/docs](http://47.253.159.62:5002/docs)
- **ReDoc**：[http://47.253.159.62:5002/redoc](http://47.253.159.62:5002/redoc)

### 🎯 MCP 接口（A2A）
- **Skill YAML**：[http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml](http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml)
- **工具列表**：[http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/list](http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/list)
- **健康检查**：[http://47.253.159.62:5002/api/v2/mcp/pdooh/health](http://47.253.159.62:5002/api/v2/mcp/pdooh/health)

### 📋 技术文档
- **接口解说**：[http://duckwolf.cn/pd.html](http://duckwolf.cn/pd.html)
- **技术博客**：[http://duckwolf.cn/cps1.html](http://duckwolf.cn/cps1.html)
- **项目白皮书**：[docs/pdoh_whitepaper_v2.md](docs/pdoh_whitepaper_v2.md)

---

## 📄 License

MIT License —— 自由使用、修改、分发。请保留原作者信息。

---

<p align="center">
  <strong>AIAdPlacer</strong> · 第一个 AI Native pDOOH 系统 · Powered by <a href="http://duckwolf.cn">duckwolf.cn</a>
</p>
