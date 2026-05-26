# AIAdPlacer - AI 智能 pDOOH 投放系统

> **AI-Powered Programmatic Digital Out-of-Home Advertising Platform**
> 基于 LLM + RAG + Agent + Workflow + MCP + 数据平台新范式

## 📋 项目简介

AIAdPlacer 是一套面向 **pDOOH（程序化户外广告）** 的 AI 原生投放系统。以「**人为锚点、点位为触点**」为核心理念，整合智能屏资产、腾讯地图 POI、讯飞 DMP 标签体系、数字联盟可信 ID、人脸识别与运营商信令数据，实现从人群洞察、智能排期、动态创意到效果归因的全链路 AI 化投放。

### 核心创新

| 特性 | 说明 |
|------|------|
| 🤖 AI 原生架构 | Agent（人群洞察/排期/创意/归因）× Workflow（规划-执行-反思）× MCP（标准化工具协议） |
| 📍 人为锚点 | 以 TAID/OAID/MAC/人脸特征 Hash 绑定唯一用户，跨屏追踪轨迹 |
| 🗺️ LBS 智能选址 | 腾讯地图 POI × 智能屏 × 人群轨迹三维匹配 |
| 🎯 55 维 DMP 标签 | 人口属性/地域/APP 兴趣/人群细分/AI 适配/媒体触达 |
| 🤝 A2A 接口 | AI-to-AI 投放模块，支持 MCP 协议与 Skill 调用，其他 AI Agent 可直连投放 |
| 📊 合规优先 | AI 投放内容 `human_visible=false`，严格遵守广告法规 |

---

## 🏗️ 系统架构

```
┌───────────┐
│                         前端层（Frontend）                          │
│  demo.html (腾讯地图可视化)  │
│  bmn-frontend/ (BMN 品牌增长系统)                                 │
└────────────────────┬──────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────┴──────────────────────────────────────┐
│                      后端 API 层（Backend）                        │
│  FastAPI (Python 3.13)                                       │
│  ├── /api/v1/*  (传统 REST API：媒体资源/投放计划/归因）             │
│  ├── /api/v2/agents/* (LangGraph Agent API）                   │
│  ├── /api/v2/rag/* (RAG 知识库 API）                         │
│  ├── /api/v2/pdooh/* (pDOOH 真实数据 API）                    │
│  └── /api/v2/mcp/*  (MCP Server：A2A 接口）                    │
└────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────┴──────────────────────────────────────┐
│                      AI 能力层（AI Layer）                         │
│  LangGraph + LangChain (Agent 编排）                              │
│  ChromaDB + sentence-transformers (RAG 向量检索）                  │
│  Ollama 本地 LLM (qwen3.5-9B）                                │
└────────────────────┬──────────────────────────────────────┘
                         │
┌────────────────────┴──────────────────────────────────────┐
│                      数据层（Data Layer）                          │
│  PostgreSQL 16 (ai_adplacer + pdooh 两个库）                     │
│  Redis 3.0.504 (缓存 + Session）                               │
│  ChromaDB (向量数据库）                                         │
└───────────────────┘
```

---

## 🗃️ 数据库设计

### pdooh 库（pDOOH 核心数据）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `screen` | 智能屏资产（9801 块） | external_id, name, lat, lng, screen_type, daily_traffic, audience_tags(JSONB) |
| `person_anchor` | 人锚点（500 人） | taid, age, gender, life_stage, home_lat, home_lng |
| `trusted_id_binding` | 可信 ID 绑定 | taid, oaid, imei_hash, mac_hash, face_feature_hash |
| `spatial_trajectory` | 空间轨迹（8979 条） | person_taid, lat, lng, screen_external_id, location_type |
| `poi_data` | POI 数据（13362 条） | poi_id, poi_name, poi_category, poi_lat, poi_lng |
| `person_dmp_tags` | 人群 DMP 标签（10000 条） | person_taid, tag_category, tag_value, confidence |
| `extended_dmp_tags` | 扩展 DMP 标签定义（55 维） | tag_category, tag_name, tag_type, data_source |
| `ai_campaign` | AI 投放计划 | campaign_id, name, target_tags(JSONB), screen_ids(JSONB) |
| `ai_ad_content` | AI 广告内容 | campaign_id, creative_type, content_hash |
| `ai_compliance_log` | AI 合规审核日志 | content_hash, human_reviewed, reject_reason |

**核心视图：**
- `vw_screen_audience`：单屏受众画像聚合（person_anchor × person_dmp_tags × spatial_trajectory）

### ai_adplacer 库（原 AIAdPlacer 数据）

| 表名 | 说明 |
|------|------|
| `media_resource` | 媒体资源（线上+线下） |
| `campaign` | 投放计划 |
| `placement` | 投放执行记录 |
| `conversion` | 转化数据 |

---

## 📡️ API 接口文档

### pDOOH 真实数据 API（`/api/v2/pdooh/`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/screens` | 查询智能屏列表（支持经纬度+半径、行政区、屏类型筛选） |
| GET | `/screens/{external_id}` | 单屏详情 |
| GET | `/screens/{id}/audience` | 单屏受众画像（年龄/性别/兴趣分布） |
| GET | `/persons` | 查询人锚点列表（支持标签筛选） |
| GET | `/persons/{taid}/tags` | 某人 DMP 标签 |
| GET | `/persons/{taid}/trajectory` | 某人轨迹 + 触屏记录 |
| GET | `/poi` | 查询 POI 列表（支持经纬度+半径、类别筛选） |
| POST | `/campaigns` | 创建投放计划 |
| GET | `/campaigns` | 投放计划列表 |
| GET | `/stats/districts` | 按行政区统计屏数量和总人流 |

#### 示例请求

```bash
# 查询广州市中心 5km 内的智能屏
curl "http://127.0.0.1:5002/api/v2/pdooh/screens?lat=23.13&lng=113.26&radius=5000&limit=20"

# 获取某屏的受众画像
curl "http://127.0.0.1:5002/api/v2/pdooh/screens/SCR-GZ-001/audience"

# 创建投放计划
curl -X POST "http://127.0.0.1:5002/api/v2/pdooh/campaigns" \
  -H "Content-Type: application/json" \
  -d '{"name":"母婴人群投放","advertiser":"某母婴品牌","target_tags":{"age_range":[25,35],"gender":"F","interests":["母婴","亲子"]},"screen_ids":["SCR-GZ-001"],"start_date":"2026-06-01","end_date":"2026-06-30","budget":50000}'
```

### Agent API（`/api/v2/agents/`）

| 路径 | 说明 |
|------|------|
| `/execute` | 执行 Agent 任务（人群洞察/排期/创意/归因） |
| `/status/{task_id}` | 查询任务执行状态 |

### RAG API（`/api/v2/rag/`）

| 路径 | 说明 |
|------|------|
| `/knowledge` | 知识库语义检索 |
| `/upload` | 上传文档到知识库 |

---

## 💻 前端 Demo

### demo.html（腾讯地图可视化）

打开 `demo.html` 即可查看：
- 🗺️ **智能屏地理分布**：腾讯地图标注 + 热力图（数据来自真实数据库）
- 📊 **核心指标卡片**：智能屏总数、覆盖行政区、日均总流量、POI 数据点、人群锚点
- 📋 **行政区统计表格**：按行政区聚合屏数量与人流
- 📃 **智能屏列表**：右侧面板展示可投放屏列表
- ➕ **新建投放计划**：弹窗输入计划名称，自动创建

**API 地址配置：**
```javascript
const API_BASE = window.location.port === '8888'
    ? '/api/v2/pdooh'   // Nginx 反代环境（端口 8888）
    : 'http://127.0.0.1:5002/api/v2/pdooh';  // 直连后端（端口 5002）
```

### 启动方式

```bash
# 启动后端（端口 5002）
cd D:\Mirofish\AIAdPlacer\backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload

# 启动 Nginx 反代（端口 8888，可选）
C:\nginx\nginx.exe -c C:\nginx\conf\nginx.conf

# 浏览器访问
# 直连：http://localhost:5002/static/demo.html
# 反代：http://localhost:8888/demo.html
```

---

## 🤝 A2A 接口（AI-to-AI 投放）

### MCP Server（Model Context Protocol）

路径：`/api/v2/mcp/pdooh`

外部 AI Agent 可通过 MCP 协议调用以下工具：

| 工具名 | 说明 |
|--------|------|
| `search_screens` | 按位置/标签搜索智能屏 |
| `get_screen_audience` | 获取某屏人群画像 |
| `create_campaign` | 创建投放计划 |
| `query_person_tags` | 查询某人 DMP 标签（可信 ID） |
| `match_audience_targeting` | AI 人群定向匹配 |

### Skill 调用模块（WorkBuddy）

安装 Skill 后，可在 WorkBuddy 中用自然语言操作 pDOOH 投放：

```
"广州天河区有哪些屏覆盖 25-35 岁女性？"
"帮我创建一个投放计划，目标人群是母婴人群，预算 5 万"
"分析北京路商圈屏的受众画像"
```

Skill 安装：
```bash
# 将 skill 文件放入 WorkBuddy skills 目录
cp -r skills/pdooh-agent/ ~/.workbuddy/skills/
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.13, FastAPI, SQLAlchemy, psycopg2 |
| AI | LangGraph, LangChain, Ollama (qwen3.5-9B), ChromaDB |
| 数据库 | PostgreSQL 16 (pdooh + ai_adplacer), Redis |
| 前端 | HTML5, CSS3, Vanilla JavaScript, 腾讯地图 GL JS API |
| 地图 | 腾讯地图 WebService API (地理编码/POI/路线规划） |
| 部署 | Nginx (反代), Windows Service (可选） |

---

## 📦 安装部署

### 1. 环境要求

- Python 3.13+
- PostgreSQL 16+ (需创建 `pdooh` 和 `ai_adplacer` 两个库）
- Redis 3.0+
- Nginx 1.20+ (可选，用于反代）

### 2. 克隆项目

```bash
git clone https://github.com/tomwugdgz/AIAdPlacer.git
cd AIAdPlacer
```

### 3. 后端环境

```bash
cd backend
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 4. 环境变量配置（`.env`）

```env
# 数据库
DATABASE_URL=postgresql://quantdinger:quantdinger123@127.0.0.1:5432/ai_adplacer
PDOOH_DATABASE_URL=postgresql://quantdinger:quantdinger123@127.0.0.1:5432/pdooh

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# 腾讯地图 API
TENCENT_MAP_KEY=7HKBZ-HQBEM-XS56X-6DBAT-ITXUZ-IDFNG

# LLM (Ollama 本地）
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=modelscope.cn/bge-m3:latest
```

### 5. 数据库初始化

```bash
# 创建 pdooh 库表结构
psql -U quantdinger -d pdooh -f docs/schema.sql
psql -U quantdinger -d pdooh -f docs/ai_ad_schema.sql

# 入库广州试点数据（547 个楼盘 + POI + 人群）
cd scripts
python geocode_tencent.py   # 地理编码
python generate_mock_data.py  # 生成模拟人群/轨迹/标签
```

### 6. 启动后端

```bash
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --port 5002 --reload
```

访问 Swagger 文档：`http://127.0.0.1:5002/docs`

---

## 📂 项目结构

```
AIAdPlacer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 主入口
│   │   ├── config.py            # 配置（环境变量）
│   │   ├── models.py           # SQLAlchemy 模型（ai_adplacer 库）
│   │   ├── pdooh_api.py      # pDOOH 真实数据 API（pdooh 库）
│   │   ├── api/
│   │   │   ├── routes.py      # v1 REST API
│   │   │   ├── agents.py     # Agent API (LangGraph)
│   │   │   └── attribution.py # 归因分析 API
│   │   └── bmn/               # BMN 品牌增长系统
│   │       ├── mcp_interface.py
│   │       └── asset_vault.py
│   └── venv/                   # Python 虚拟环境
├── demo.html                    # 前端 Demo（腾讯地图可视化）
├── docs/
│   ├── schema.sql             # pDOOH 数据库 Schema
│   ├── ai_ad_schema.sql      # AI 投放模块 Schema
│   └── extended_tags.sql     # 扩展 DMP 标签
├── scripts/
│   ├── geocode_tencent.py  # 腾讯地图批量地理编码
│   └── generate_mock_data.py # 模拟数据生成器
├── skills/
│   └── pdooh-agent/          # WorkBuddy Skill（自然语言操作 pDOOH）
└── README.md
```

---

## 📊 数据来源说明

| 数据类型 | 来源 | 记录数 |
|----------|------|--------|
| 智能屏资产 | 广州试点楼盘（人工整理） | 547 个楼盘 → 9801 块屏（模拟扩展） |
| POI 数据 | 高保真模拟（基于行政区密度规则） | 13,362 条 |
| 人群锚点 | 模拟生成（基于楼盘人口统计） | 500 人 |
| DMP 标签 | 模拟生成（55 维标签体系） | 10,000 条 |
| 空间轨迹 | 模拟生成（家-工作-屏三段式轨迹） | 8,979 条 |

> **注**：当前为广州试点阶段，使用模拟数据验证架构可行性。接入真实数据需对接：
> - 数字联盟可信 ID SDK
> - 人脸识别设备数据（海康/大华）
> - 运营商信令数据（移动/联通/电信）
> - 讯飞 DMP API

---

## 🚨 合规声明

本系统严格遵守《广告法》《个人信息保护法》《数据安全法》：

1. **AI 投放内容标注**：所有 AI 生成内容均通过 `ai_compliance_log` 表记录审核状态
2. **可信 ID 去标识化**：人脸特征、MAC、IMEI 均做 Hash 处理，不复原原始值
3. **数据最小化**：仅收集投放必需数据，支持用户「被遗忘权」
4. **AI-to-AI 内容不可见**：`human_visible=false` 的投放内容仅 AI Agent 可读取

---

## 📧 联系方式

- 项目地址：<ADDRESS_REMOVED>
- 问题反馈：<ADDRESS_REMOVED>
- 个人网站：<ADDRESS_REMOVED>

---

## 📝 更新日志

### v2.0.0 (2026-05-27)
- ✅ 完成 pDOOH 数据库 Schema 设计（12 张表 + 2 视图）
- ✅ 完成广州 547 个楼盘地理编码（100% 成功）
- ✅ 入库 13,362 条高保真 POI 数据
- ✅ 生成 500 人锚点 + 10,000 条 DMP 标签 + 8,979 条轨迹
- ✅ 创建 `pdooh_api.py` 真实数据 API（9 个端点）
- ✅ 改造 `demo.html` 连接真实数据库（替换所有模拟数据）
- ✅ 编写详细 README.md
- 🔄 A2A MCP Server（进行中）
- 🔄 Skill 调用模块（进行中）

### v1.0.0 (2026-03-XX)
- 初始版本：AIAdPlacer 基础投放系统
- LangGraph Agent 编排
- ChromaDB RAG 知识库
- BMN 品牌增长系统
