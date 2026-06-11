# AIAdPlacer 产品完整规格说明书

> **文档版本**：v2.2 · 2026-06  
> **编写目的**：为 AI 系统提供足够详细的产品规格，使其能独立重新实现一套同类软件系统。  
> **覆盖范围**：产品定位、核心概念、系统架构、功能模块、用户流程、AI Agent 逻辑、数据模型、API 规范、MCP 集成、部署架构、行业对标、改进方向。

---

## 目录

1. [产品概述](#1-产品概述)
2. [核心业务概念](#2-核心业务概念)
3. [系统架构](#3-系统架构)
4. [功能模块详解](#4-功能模块详解)
5. [用户使用流程](#5-用户使用流程)
6. [AI Agent 编排逻辑](#6-ai-agent-编排逻辑)
7. [数据模型](#7-数据模型)
8. [API 完整规范](#8-api-完整规范)
9. [MCP/A2A 集成](#9-mcpa2a-集成)
10. [部署与运维](#10-部署与运维)
11. [行业标准对齐](#11-行业标准对齐)
12. [产品评价：喜欢与改进空间](#12-产品评价喜欢与改进空间)
13. [附录：术语表](#13-附录术语表)

---

## 1. 产品概述

### 1.1 产品定位

**AIAdPlacer** 是全球首个 AI Native 的 pDOOH（程序化数字户外广告）智能投放平台。

| 维度 | 说明 |
|------|------|
| 核心价值 | 帮广告主做投放决策、帮媒体主管理库存、帮代理商提升效率 |
| 技术特色 | 第一个将 LLM + Agent + RAG + Workflow + MCP 完整落地的 pDOOH 系统 |
| 数据底座 | 亲邻科技 5V 数据模型（人口/消费/社区/门禁/行为） |
| 差异化优势 | V4 门禁数据——每次「开门」都是一次真实到店验证 |

### 1.2 目标用户

| 用户角色 | 痛点 | 产品提供的价值 |
|----------|------|----------------|
| 广告主 | 不知道投哪里、效果不可测 | AI 推荐点位 + OTC 归因模型 |
| 媒体主 | 库存利用率低、定价不透明 | AI 排期优化 + 动态定价 |
| 代理商 | 报告制作耗时、竞品不透明 | AI 自动报告 + 竞品监控 |
| AI Agent | 无法调用户外广告能力 | A2A/MCP 标准接口 |

### 1.3 技术栈概览

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI（Python 3.13） |
| Agent 编排 | LangGraph + LangChain |
| 向量数据库 | ChromaDB |
| 嵌入模型 | sentence-transformers（text2vec-base-chinese） |
| 关系数据库 | PostgreSQL 16 |
| 缓存 | Redis 3.0 |
| 地图服务 | 腾讯地图 WebService API |
| 前端 | 原生 HTML/CSS/JS（SPA，Nginx 反向代理） |
| 部署 | Windows Server（当前）/ Linux（推荐生产） |

---

## 2. 核心业务概念

### 2.1 pDOOH（程序化数字户外广告）

```
传统户外广告           pDOOH（程序化户外广告）
------------------------------------------------
人工谈判 → 合同      AI 推荐 → 自动竞价 → 程序化投放
效果不可测             OTC 归因模型（可量化）
静态创意               动态创意（DCO + AIGC）
单一媒体               跨媒体组合（道闸+单元门+LED）
```

### 2.2 亲邻科技 5V 数据模型

| V层 | 数据维度 | 业务价值 | 独家性 |
|-----|----------|----------|--------|
| V1 人口属性 | 年龄/性别/学历/收入 | 基础人群定向 | 通用 |
| V2 消费偏好 | DMP 标签 | 精准兴趣投放 | 通用 |
| V3 社区属性 | 楼盘/户型/房价 | 社区价值评估 | 行业特有 |
| V4 门禁动作 ★ | 扫码/刷脸记录 | 真实到店证据 | **独家** |
| V5 线上行为 | APP 使用轨迹 | 跨屏人群扩展 | 通用 |

**V4 门禁数据是核心护城河**：每次居民扫码/刷脸开门，都产生一条带时间戳的到店记录，可用于验证广告曝光后的到店转化。

### 2.3 OTC 模型（Opportunity To Contact）

```
OTC = PV × Reach × Frequency × 有效接触系数
```

| 参数 | 说明 | 数据来源 |
|------|------|----------|
| PV | 页面浏览量（上限约束） | 腾讯地图 API / 硬件传感器 |
| Reach | 触达人数 | OneID 去重统计 |
| Frequency | 触达频次 | 500米网格曝光计数 |
| 有效接触系数 | 广告有效触达比例 | AI 模型估算（0.3–0.8） |

### 2.4 社区广告资源类型

| 资源类型 | 位置 | 受众场景 | 适合行业 |
|----------|------|----------|----------|
| 单元门灯箱 | 电梯厅/楼道 | 回家动线，高频低注意 | 快消、母婴 |
| 广告门（道闸） | 小区出入口 | 进出必看，强制曝光 | 汽车、地产 |
| 开门App | 手机端 | 开门瞬间，高注意力 | 本地生活、O2O |
| 社区LED | 广场/活动区 | 广场舞/活动场景 | 政府、大型品牌 |

---

## 3. 系统架构

### 3.1 整体架构（文字描述）

```
┌─────────────────────────────────────────────────────────┐
│                   用户交互层                              │
│  Web Dashboard / 广告主Portal / 代理商CRM               │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI 后端服务（v2.0.0 CPS）           │
│  /api/v2/agents/*  ·  /api/v2/rag/*  ·  /api/v2/mcp/*│
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              AI Agent 编排层（LangGraph）                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │人群洞察   │ │智能排期   │ │动态创意   │ │效果归因   │ │
│  │Agent      │ │Agent      │ │Agent      │ │Agent      │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│            统一编排 Agent（规划→执行→反思）                │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              数据与服务层                                  │
│  PostgreSQL │ Redis │ ChromaDB │ 腾讯地图API │ 5V数据  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 目录结构

```
AIAdPlacer/
├── main.py                  # FastAPI 入口，注册路由
├── agents/                  # LangGraph Agent 定义
│   ├── base_agent.py        # Agent 基类
│   ├── audience_insight.py # 人群洞察 Agent（KMeans）
│   ├── schedule_optimizer.py # 智能排期 Agent（FM+deepMCP）
│   ├── creative_generator.py # 动态创意 Agent（AIGC+DCO）
│   ├── attribution_agent.py # 效果归因 Agent（跨端匹配）
│   └── orchestrator.py     # 统一编排 Agent
├── rag/                     # RAG 检索增强生成
│   ├── vector_store.py      # ChromaDB 封装
│   ├── embedding_model.py  # text2vec 封装
│   └── retriever.py        # 检索器
├── api/                     # API 路由
│   └── v2/                 # CPS 2.0 API
│       ├── agents.py        # Agent 调用接口
│       ├── rag.py           # RAG 查询接口
│       └── mcp.py          # MCP 工具接口
├── models/                  # SQLAlchemy 模型
│   ├── user.py
│   ├── campaign.py         # 投放计划
│   ├── creative.py         # 创意素材
│   ├── inventory.py        # 媒体库存
│   └── otc_log.py         # OTC 归因日志
├── data/                    # 5V 数据层
│   ├── v1_demographic.py
│   ├── v2_consumption.py
│   ├── v3_community.py
│   ├── v4_access.py       # 门禁数据（核心）
│   └── v5_behavior.py
├── static/                  # 前端静态文件
│   ├── index.html          # 主界面
│   ├── cps2-demo.html     # CPS 2.0 演示页面
│   ├── css/
│   └── js/
└── requirements.txt
```

---

## 4. 功能模块详解

### 4.1 人群洞察模块

**目标**：帮广告主找到最适合的投放社区和人群。

**核心算法**：KMeans 聚类（scikit-learn）
- 输入：V1–V5 五维数据
- 输出：社区人群聚类标签（如「年轻家庭型」「高收入商务型」）
- 可视化：社区分布热力图（调用腾讯地图 JS API）

**API 端点**：`POST /api/v2/agents/audience-insight`

**请求示例**：

```json
{
  "brand": "宝马",
  "target": "35-45岁，家庭年收入>50万，有车",
  "cities": ["深圳", "广州"],
  "budget": 500000
}
```

**响应示例**：

```json
{
  "clusters": [
    {
      "label": "高端社区集群",
      "community_count": 127,
      "avg_house_price": 850000,
      "match_score": 0.89
    }
  ],
  "recommended_communities": ["翡翠花园", "香蜜湖一号"],
  "estimated_otc": 1250000
}
```

### 4.2 智能排期模块

**目标**：在预算约束下，找到最优的投放时间和媒体组合。

**核心算法**：FM（Factorization Machines）+ deepMCP（深度多任务学习）
- FM：捕捉媒体属性和时间的特征交互
- deepMCP：同时优化曝光（Exposure）、点击（Click）、转化（Conversion）三个目标

**排期约束**：
- 预算上限
- 时间窗口（投放开始/结束日期）
- 媒体类型组合（道闸/单元门/App）
- 频控（每人每天最多 N 次）

**API 端点**：`POST /api/v2/agents/schedule-optimizer`

### 4.3 动态创意模块

**目标**：根据受众特征，实时生成/选择最合适的广告创意。

**核心能力**：
- AIGC：用 LLM 生成广告文案（支持自定义品牌语调）
- DCO（Dynamic Creative Optimization）：根据实时反馈调整创意组合
- 多模态：支持图片+文案+CTA 按钮的组合优化

**创意模板示例**：

```
输入：品牌=宝马，车型=X5，受众=高收入商务型
输出：
  - 文案：「驾驭非凡，X5 伴您征服每一程」
  - 视觉：深色背景+车灯特写
  - CTA：「预约试驾」
```

**API 端点**：`POST /api/v2/agents/creative-generator`

### 4.4 效果归因模块

**目标**：量化广告投放的实际效果（到店、转化）。

**核心方法**：跨端匹配
- 将广告曝光日志（OTC 数据）与门禁扫码记录（V4 数据）进行 ID 匹配
- 计算 CAC（Customer Acquisition Cost）和 ROAS（Return on Ad Spend）

**归因窗口**：曝光后 7 天内到店视为有效转化。

**API 端点**：`POST /api/v2/agents/attribution`

### 4.5 RAG 知识库模块

**目标**：让 Agent 能查询行业知识、历史案例、竞品信息。

**知识库来源**：
- 行业报告（pDOOH、户外广告）
- 历史投放案例
- 竞品素材库
- 亲邻科技内部 SOP

**检索流程**：
1. 用户问题 → 向量化（text2vec-base-chinese）
2. ChromaDB 相似度检索（top-k=5）
3. 将检索结果注入 LLM prompt
4. 生成回答

**API 端点**：`POST /api/v2/rag/query`

---

## 5. 用户使用流程

### 5.1 广告主投放流程（主要流程）

```
[1. 注册/登录]
      │
      ▼
[2. 创建投放计划]
   - 选择品牌/产品
   - 定义目标人群（年龄/收入/兴趣）
   - 设置预算和时间窗口
      │
      ▼
[3. AI 推荐点位]
   - 调用人群洞察 Agent
   - 返回推荐社区列表 + 预估 OTC
   - 用户调整选择
      │
      ▼
[4. AI 生成排期]
   - 调用智能排期 Agent
   - 返回最优媒体组合 + 时间安排
      │
      ▼
[5. AI 生成创意]
   - 调用动态创意 Agent
   - 生成多套创意方案
   - 用户选择/修改
      │
      ▼
[6. 确认并支付]
   - 系统生成合同（AI 辅助起草）
   - 在线支付（微信支付/银行转账）
      │
      ▼
[7. 投放执行]
   - 系统自动下发投放指令到媒体终端
   - 实时监控曝光数据
      │
      ▼
[8. 效果报告]
   - 调用效果归因 Agent
   - 生成可视化报告（含 OTC 数据）
   - 支持导出 PDF/Excel
```

### 5.2 代理商管理系统

代理商可以：
- 管理多个广告主账户
- 查看所有下属广告主的投放数据
- 使用 AI 批量生成投放建议报告
- 监控竞品投放动态（AI 自动抓取分析）

---

## 6. AI Agent 编排逻辑

### 6.1 统一编排 Agent（Orchestrator）

```
用户请求
    │
    ▼
[规划阶段]  Orchestrator 分析请求，决定调用哪些 Agent
    │
    ├─→ 需要人群分析？  ─→ 调用 AudienceInsightAgent
    ├─→ 需要排期优化？  ─→ 调用 ScheduleOptimizerAgent
    ├─→ 需要创意生成？  ─→ 调用 CreativeGeneratorAgent
    └─→ 需要归因分析？  ─→ 调用 AttributionAgent
    │
    ▼
[执行阶段]  各 Agent 并行或串行执行（根据依赖关系）
    │
    ▼
[反思阶段]  Orchestrator 检查执行结果
    │
    ├─→ 结果满意？  ─→ 返回用户
    └─→ 不满意？    ─→ 调整参数，重新执行（最多 3 轮）
```

### 6.2 Agent 通信协议

- Agent 之间使用 **结构化 JSON** 传递数据
- 每个 Agent 的输入/输出都有 **JSON Schema** 定义
- Orchestrator 负责数据格式转换和错误重试

**Agent 输出 Schema 示例**：

```json
{
  "agent_name": "AudienceInsightAgent",
  "status": "success",
  "data": {
    "clusters": [...],
    "recommendations": [...]
  },
  "reasoning": "基于 V1-V5 数据分析，推荐高端社区集群...",
  "confidence": 0.89
}
```

---

## 7. 数据模型

### 7.1 核心数据库表（PostgreSQL）

#### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| email | VARCHAR | 登录邮箱 |
| role | ENUM | advertiser/agent/admin |
| company | VARCHAR | 公司名称 |
| created_at | TIMESTAMP | 创建时间 |

#### campaigns（投放计划表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键 → users |
| name | VARCHAR | 计划名称 |
| brand | VARCHAR | 品牌名称 |
| budget | DECIMAL | 预算（元） |
| start_date | DATE | 开始日期 |
| end_date | DATE | 结束日期 |
| status | ENUM | draft/active/paused/completed |
| created_at | TIMESTAMP | 创建时间 |

#### creatives（创意素材表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| campaign_id | UUID | 外键 → campaigns |
| type | ENUM | image/text/video |
| content | JSON | 创意内容（文案/图片URL/CTA） |
| performance_score | FLOAT | AI 预测的点击率 |

#### otc_logs（OTC 归因日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| campaign_id | UUID | 外键 → campaigns |
| user_id | VARCHAR | 匿名用户 ID（OneID） |
| community_id | VARCHAR | 社区 ID |
| touch_time | TIMESTAMP | 曝光时间 |
| convert_time | TIMESTAMP | 到店时间（nullable） |
| otc_value | FLOAT | OTC 贡献值 |

### 7.2 5V 数据层接口

每个 V 层数据通过统一的 `DataProvider` 接口访问：

```python
from abc import ABC, abstractmethod
import pandas as pd

class DataProvider(ABC):
    @abstractmethod
    def query(self, filters: dict) -> pd.DataFrame:
        """根据过滤条件查询数据"""
        pass

    @abstractmethod
    def get_coverage(self, city: str) -> float:
        """返回数据在城市中的覆盖率"""
        pass
```

---

## 8. API 完整规范

### 8.1 认证

所有 API 请求需要在 Header 中携带 API Key：

```
X-API-Key: <your_api_key>
```

### 8.2 Agent 调用 API

#### POST /api/v2/agents/{agent_name}/invoke

**请求体**（通用）：

```json
{
  "input": {
    // Agent 特定的输入参数
  },
  "context": {
    "user_id": "xxx",
    "campaign_id": "xxx",
    "session_id": "xxx"
  }
}
```

**响应体**（通用）：

```json
{
  "task_id": "xxx",
  "status": "pending|running|completed|failed",
  "result": {
    // Agent 特定的输出
  },
  "reasoning_trace": [
    // Agent 的思考链路（可解释性）
  ]
}
```

#### 支持的 agent_name：

- `audience-insight`：人群洞察
- `schedule-optimizer`：智能排期
- `creative-generator`：动态创意
- `attribution`：效果归因
- `orchestrator`：统一编排（自动调动以上所有）

### 8.3 RAG 查询 API

#### POST /api/v2/rag/query

```json
{
  "query": "深圳高端社区有哪些？",
  "top_k": 5,
  "filters": {
    "source": "internal_report",
    "date_range": ["2025-01-01", "2026-06-01"]
  }
}
```

**响应**：

```json
{
  "results": [
    {
      "content": "...",
      "metadata": {
        "source": "internal_report_2025.pdf",
        "page": 12
      },
      "score": 0.89
    }
  ],
  "answer": "根据知识库，深圳高端社区主要集中在..."
}
```

### 8.4 MCP 工具 API

#### POST /api/v2/mcp/tools/list

返回所有可用的 MCP 工具列表（供 AI Agent 调用）。

#### POST /api/v2/mcp/tools/invoke

```json
{
  "tool_name": "search_community",
  "parameters": {
    "city": "深圳",
    "min_price": 500000
  }
}
```

---

## 9. MCP/A2A 集成

### 9.1 MCP（Model Context Protocol）

MCP 是一个让 AI Agent 能调用外部工具的标准协议。

**AIAdPlacer 提供的 MCP 工具**：

- `search_community`：搜索符合条件的社区
- `estimate_otc`：预估投放 OTC
- `generate_creative`：生成广告创意
- `query_campaign`：查询投放计划状态
- `get_attribution_report`：获取归因报告

**MCP Server 实现**：
- 基于 FastAPI 实现 MCP 兼容接口
- 支持 SSE（Server-Sent Events）流式返回
- 工具定义使用 JSON Schema

### 9.2 A2A（Agent-to-Agent）协议

A2A 是 Google 提出的 Agent 互操作协议。

**AIAdPlacer 的 A2A 实现**：
- 暴露 Agent Card（Agent 能力描述文件）
- 支持 Agent 发现（Agent Discovery）
- 支持异步任务（Async Task）
- 支持流式进度更新

**Agent Card 示例**（`/.well-known/agent.json`）：

```json
{
  "name": "AIAdPlacer",
  "description": "pDOOH 智能投放 Agent",
  "version": "2.0.0",
  "capabilities": [
    "audience_insight",
    "schedule_optimization",
    "creative_generation",
    "attribution_analysis"
  ],
  "authentication": {
    "type": "api_key"
  },
  "api_endpoint": "https://api.aiadplacer.com/api/v2/"
}
```

---

## 10. 部署与运维

### 10.1 部署架构

```
                    ┌─────────────────┐
                    │   Nginx（反向代理）│
                    │   SSL 终止        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
       │ FastAPI #1  │ │ FastAPI #2 │ │ FastAPI #3│
       │ (workers)   │ │ (workers)  │ │ (workers) │
       └──────┬─────┘ └─────┬──────┘ └────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
       │ PostgreSQL   │ │   Redis    │ │ ChromaDB │
       │ (主从)      │ │  (哨兵)    │ │ (持久化) │
       └────────────┘ └────────────┘ └──────────┘
```

### 10.2 环境变量配置

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_adplacer

# Redis
REDIS_URL=redis://localhost:6379

# 腾讯地图
TENCENT_MAP_API_KEY=your_key_here

# LLM（支持多种后端）
LLM_PROVIDER=openai  # 或 anthropic/azure/gemini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# MCP
MCP_SERVER_URL=http://localhost:5002/api/v2/mcp

# 安全
API_KEY_SECRET=your_secret_here
JWT_SECRET=your_jwt_secret
```

### 10.3 监控与告警

- **应用监控**：Prometheus + Grafana
- **日志**：结构化 JSON 日志，接入 ELK
- **告警规则**：
  - API 错误率 > 5% → 触发告警
  - Agent 执行时间 > 30s → 记录慢查询
  - 数据库连接池 > 80% → 扩容提醒

---

## 11. 行业标准对齐

### 11.1 T/CCSA 738-2025 标准

AIAdPlacer 参考中国通信标准化协会（CCSA）发布的《程序化户外广告投放系统技术要求》标准（T/CCSA 738-2025）。

**对齐要点**：
- 支持 OpenRTB 协议扩展（pDOOH 专用字段）
- 曝光测量基于 OTC 模型（符合标准定义的「可见曝光」）
- 数据隐私符合《个人信息保护法》（PIPL）

### 11.2 国际对标

| 国际标准 | 对应 AIAdPlacer 实现 |
|----------|----------------------|
| IAB OpenRTB 3.0 | 支持 Bid Request/Response 扩展 |
| OMA（Outdoor Media Association）标准 | 媒体库存描述规范 |
| GDPR（欧盟） | 数据匿名化 + 用户同意管理 |
| PIPL（中国） | 个人信息去标识化 |

---

## 12. 产品评价：喜欢与改进空间

### 12.1 产品亮点（喜欢的部分）

**1. AI Native 设计理念**

- 不是在传统系统上「加 AI」，而是从零开始以 Agent 为核心设计
- LangGraph 编排使得 Agent 协作可解释、可调试

**2. 5V 数据模型的独特价值**

- V4 门禁数据是真正的竞争壁垒
- 到店验证让户外广告效果可量化（这是行业痛点）

**3. MCP/A2A 的前瞻性**

- 提前布局 Agent 互操作协议
- 让产品可以成为更大型 AI 系统的「工具」

**4. OTC 模型的实用性**

- 比传统的「千人成本（CPT）」更科学
- 可以直接对标数字广告的 ROI 计算方式

### 12.2 改进空间（可以更好的部分）

#### 12.2.1 数据隐私与合规

**问题**：V4 门禁数据涉及居民出入记录，隐私风险极高。

**改进建议**：

- 实施「数据可用不可见」方案（联邦学习 / 多方安全计算）
- 门禁数据只保留聚合统计，不存储个人行为轨迹
- 获取居民明确授权（opt-in），而非默认采集

#### 12.2.2 Agent 可靠性

**问题**：LLM 生成结果存在不确定性，可能导致投放建议不合理。

**改进建议**：

- 引入「人在回路」（Human-in-the-Loop）：关键决策需要人工确认
- Agent 输出增加置信度评分，低置信度时自动触发人工审核
- 建立 Agent 决策日志，便于事后审计

#### 12.2.3 创意生成质量

**问题**：当前 AIGC 生成的文案/图片质量不稳定，需要大量人工筛选。

**改进建议**：

- 建立创意质量评估模型（基于历史点击率数据训练）
- 引入 A/B 测试框架：创意上线后自动分配流量测试，优胜劣汰
- 支持品牌方上传自有创意素材，AI 只做优化建议

#### 12.2.4 跨屏归因精度

**问题**：OTC 归因依赖 ID 匹配，但用户可能使用不同设备/账号。

**改进建议**：

- 引入概率归因模型（Probabilistic Attribution）
- 结合腾讯/字节的跨屏 ID 映射能力
- 使用因果推断（Causal Inference）方法分离广告效应

#### 12.2.5 系统性能与成本

**问题**：LLM 调用成本高，并发量大时响应慢。

**改进建议**：

- 实施 LLM 缓存策略（相似请求直接返回缓存结果）
- 使用小模型（如 Qwen3.5-9B）处理简单任务，大模型只用于复杂推理
- 批量处理：将多个广告主的请求合并，提高 GPU 利用率

#### 12.2.6 用户体验

**问题**：当前前端是简单的 HTML 页面，缺少现代 SaaS 产品的交互体验。

**改进建议**：

- 使用 React + Ant Design Pro 重构前端
- 增加拖拽式投放计划编辑器
- 实时数据大屏（WebSocket 推送）
- 移动端 App（广告主随时查看投放数据）

#### 12.2.7 生态建设

**问题**：目前只有亲邻科技自己的媒体资源，覆盖面有限。

**改进建议**：

- 开放媒体主接入 API，让更多社区媒体加入
- 建立 pDOOH 联盟链（区块链记录投放数据，防止作弊）
- 与电商平台合作，实现「看到广告 → 到店 → 购买」的全链路追踪

---

## 13. 附录：术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| pDOOH | Programmatic Digital Out-of-Home | 程序化数字户外广告 |
| OTC | Opportunity To Contact | 机会接触模型，衡量广告曝光价值 |
| DCO | Dynamic Creative Optimization | 动态创意优化 |
| AIGC | AI Generated Content | AI 生成内容 |
| RAG | Retrieval-Augmented Generation | 检索增强生成 |
| MCP | Model Context Protocol | AI Agent 工具调用协议 |
| A2A | Agent-to-Agent | Agent 互操作协议 |
| LLM | Large Language Model | 大语言模型 |
| OneID | - | 跨设备用户统一标识 |
| CPT | Cost Per Thousand | 千人成本（传统户外广告计价） |
| CPM | Cost Per Mille | 千次曝光成本 |
| ROAS | Return on Ad Spend | 广告支出回报率 |
| CAC | Customer Acquisition Cost | 客户获取成本 |
| PIPL | Personal Information Protection Law | 中国个人信息保护法 |
| OpenRTB | - | 程序化广告竞价协议标准 |

---

## 附录：重新实现指南（给 AI 开发者的说明）

如果您是一位 AI 开发者，希望基于本文档重新实现一个类似的系统，以下是建议的技术路线：

### A. 最小可行产品（MVP）功能清单

1. 用户注册/登录（可以用 Auth0 或 Supabase Auth）
2. 社区数据上传 + 管理（CSV 导入即可）
3. 基于规则的推荐（先不用 AI，用 SQL 查询 + 规则引擎）
4. 投放计划创建 + 管理
5. 基础报告（Excel 导出）

### B. 逐步添加 AI 能力

1. 先接一个 LLM（OpenAI API 或国内大模型 API）
2. 实现 RAG：上传几份行业报告，让系统能回答简单问题
3. 实现第一个 Agent（人群洞察）：用 LLM 分析上传的社区数据
4. 添加更多 Agent，用 LangGraph 编排
5. 实现 MCP 接口，让外部 AI 能调用你的系统

### C. 关键开源组件推荐

| 功能 | 推荐组件 |
|------|----------|
| API 框架 | FastAPI（Python）/ Express（Node.js） |
| Agent 编排 | LangGraph / AutoGen / CrewAI |
| 向量数据库 | ChromaDB（本地）/ Pinecone（云端） |
| 嵌入模型 | text2vec-base-chinese（中文）/ all-MiniLM-L6-v2（英文） |
| 数据库 | PostgreSQL + PostGIS（地理数据） |
| 任务队列 | Celery + Redis |
| 前端 | React + Tailwind CSS |

### D. 数据获取建议

- **社区数据**：可以从公开数据平台（如高德地图 POI、链家房价数据）获取
- **门禁数据**：这是独家数据，重新实现时可以用「到店打卡」或「WiFi 连接记录」替代
- **户外广告标准**：参考 IAB 和 CCSA 的公开标准文档

---

*文档结束 — 如需补充任何章节，请联系产品团队。*