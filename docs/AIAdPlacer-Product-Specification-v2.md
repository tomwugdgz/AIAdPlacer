# AIAdPlacer 产品完整规格说明书（增强版）

> **文档版本**：v2.3 · 2026-06  
> **编写目的**：为 AI 系统提供足够详细的产品规格，使其能独立重新实现一套同类软件系统。  
> **更新说明**：v2.3 新增算法数学公式、完整代码示例、DDL SQL、API 客户端示例。

---

## 目录

1. [产品概述](#1-产品概述)
2. [核心业务概念与数学模型](#2-核心业务概念与数学模型)
3. [系统架构](#3-系统架构)
4. [功能模块详解（含算法公式）](#4-功能模块详解含算法公式)
5. [用户使用流程](#5-用户使用流程)
6. [AI Agent 编排逻辑与代码](#6-ai-agent-编排逻辑与代码)
7. [数据模型（含 DDL）](#7-数据模型含-ddl)
8. [API 完整规范与客户端示例](#8-api-完整规范与客户端示例)
9. [MCP/A2A 集成](#9-mcpa2a-集成)
10. [部署与运维](#10-部署与运维)
11. [行业标准对齐](#11-行业标准对齐)
12. [产品评价：喜欢与改进空间](#12-产品评价喜欢与改进空间)
13. [附录：术语表与重新实现指南](#13-附录术语表与重新实现指南)

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

## 2. 核心业务概念与数学模型

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

### 2.3 OTC 模型（Opportunity To Contact）—— 完整数学定义

#### 2.3.1 基础公式

```
OTC_total = SUM_over_all_grids( PV_grid × Reach_grid × Frequency_grid × Alpha_grid )
```

其中：

- **PV（Page View，曝光量）**：该网格内广告位每日被「看到」的次数上限。
  - 计算方式：`PV = SUM(Device_Count × Daily_Impression_Per_Device)`
  - `Device_Count`：社区内广告设备数量
  - `Daily_Impression_Per_Device`：单设备每日可产生的有效曝光次数（道闸：进出各1次；单元门：每日平均3次）

- **Reach（触达人数）**：
  - 定义：至少看到广告一次的去重人数
  - 计算：`Reach = PV × (1 - e^(-lambda × Unique_Rate))`
  - `lambda`：广告位到门口的平均距离衰减系数（0.05–0.30）
  - `Unique_Rate`：该社区实有人口 / 设备覆盖人数

- **Frequency（触达频次）**：
  - 定义：平均每人看到广告的次数
  - 计算：`Frequency = PV / Reach`
  -  capped at 7（超过7次视为无效重复曝光，按7计算）

- **Alpha（有效接触系数，0.0–1.0）**：
  - 由 AI 模型预测，输入特征包括：
    - 广告形式（道闸=0.85，单元门=0.45，App开屏=0.70）
    - 时段（早高峰7–9点=0.75，晚高峰17–20点=0.80，其他=0.40）
    - 天气（晴=1.0，雨=0.60，霾=0.50）
  - 预测模型：`Alpha = sigmoid(W × features + b)` （轻量级逻辑回归，离线训练）

#### 2.3.2 归因校准

OTC 预测值需用 V4 门禁数据校准：

```
OTC_calibrated = OTC_predicted × (Actual_Visits / Predicted_Visits)
```

校准窗口：广告投放后 7 天内到店记录。

#### 2.3.3 与 CPT 的对比

| 指标 | 传统 CPT | OTC 模型 |
|------|------------|---------|
| 计算基础 | 估算总人流 | 可验证的到店人次 |
| 精度 | 低（±40%） | 高（±15%，有V4校准） |
| 可优化性 | 不可优化 | 可实时调整投放参数 |
| 计费公平性 | 对媒体主有利 | 对广告主有利 |

### 2.4 社区广告资源类型

| 资源类型 | 位置 | 受众场景 | 适合行业 | OTC权重 |
|----------|------|----------|----------|---------|
| 单元门灯箱 | 电梯厅/楼道 | 回家动线，高频低注意 | 快消、母婴 | 0.45 |
| 广告门（道闸） | 小区出入口 | 进出必看，强制曝光 | 汽车、地产 | 0.85 |
| 开门App | 手机端 | 开门瞬间，高注意力 | 本地生活、O2O | 0.70 |
| 社区LED | 广场/活动区 | 广场舞/活动场景 | 政府、大型品牌 | 0.55 |

---

## 3. 系统架构

### 3.1 整体架构图

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

### 3.2 目录结构（完整版）

```
AIAdPlacer/
├── main.py                  # FastAPI 入口，注册路由
├── config.py                # 全局配置（环境变量读取）
├── agents/                  # LangGraph Agent 定义
│   ├── base_agent.py        # Agent 基类（含重试、日志、Schema校验）
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
├── tests/                   # 测试文件
│   ├── test_agents.py
│   └── test_api.py
└── requirements.txt
```

---

## 4. 功能模块详解（含算法公式）

### 4.1 人群洞察模块

**目标**：帮广告主找到最适合的投放社区和人群。

#### 算法：KMeans 聚类

**目标函数**（最小化簇内平方和）：

```
J = SUM_over_k( SUM_over_i_in_Ck( ||x_i - mu_k||^2 ) )
```

其中：
- `C_k`：第 k 个簇
- `mu_k`：第 k 个簇的中心向量
- `x_i`：第 i 个样本的 5V 特征向量

**特征向量维度**（示例）：

```python
# 每个社区用以下特征向量表示（归一化后）
feature_vector = [
    v1_avg_age,           # V1: 平均年龄（归一化）
    v1_avg_income,        # V1: 平均收入（归一化）
    v2_consumption_level,  # V2: 消费力指数 0-1
    v3_avg_house_price,   # V3: 平均房价（归一化）
    v3_property_type,      # V3: 楼盘类型（编码）
    v4_daily_access,      # V4: 日均门禁次数
    v5_app_usage_score,    # V5: APP使用偏好得分
]
```

**KMeans 参数选择**：
- 使用肘部法则（Elbow Method）确定最优 K
- 当前生产环境 K=8（对应8类社区人群）
- 距离度量：欧氏距离

#### 完整代码示例

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

def cluster_communities(df: pd.DataFrame, n_clusters: int = 8):
    # df columns: community_id, v1_age, v1_income, v2_consumption,
    #                v3_house_price, v4_daily_access, v5_app_score
    
    # 1. 特征提取与归一化
    features = df[['v1_age', 'v1_income', 'v2_consumption',
                 'v3_house_price', 'v4_daily_access', 'v5_app_score']].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # 2. KMeans 聚类
    kmeans = KMeans(
        n_clusters=n_clusters,
        init='k-means++',
        n_init=10,
        max_iter=300,
        random_state=42
    )
    labels = kmeans.fit_predict(features_scaled)
    
    # 3. 为每个簇生成标签（基于特征均值）
    df_result = df.copy()
    df_result['cluster'] = labels
    
    cluster_labels = {}
    for k in range(n_clusters):
        cluster_data = df_result[df_result['cluster'] == k]
        avg_income = cluster_data['v1_income'].mean()
        avg_age = cluster_data['v1_age'].mean()
        if avg_income > 50000:
            label = f'高端社区集群_k{k}'
        elif avg_age < 35:
            label = f'年轻家庭集群_k{k}'
        else:
            label = f'综合社区集群_k{k}'
        cluster_labels[k] = label
    
    return df_result, cluster_labels, kmeans
```

**API 端点**：`POST /api/v2/agents/audience-insight`

---

### 4.2 智能排期模块

**目标**：在预算约束下，找到最优的投放时间和媒体组合。

#### 算法：Factorization Machines（FM）

**预测公式**：

```
y_hat(x) = w_0 + SUM_i(w_i * x_i) + SUM_iSUM_j<i( <v_i, v_j> * x_i * x_j )
```

其中：
- `w_0`：全局偏置
- `w_i`：第 i 个特征的权重
- `v_i`：第 i 个特征的隐向量（维度 k，通常 k=10）
- `<v_i, v_j>`：隐向量的内积，捕捉特征 i 和 j 的交互

**为什么用 FM**：
- 户外广告数据稀疏（很多社区×时段组合没有历史数据）
- FM 通过隐向量能有效估计稀疏特征组合
- 预测复杂度 O(kn)，适合实时排期

#### 深度多任务学习（deepMCP）

同时优化三个目标：

```
Loss = alpha * L_exposure + beta * L_click + gamma * L_conversion
```

其中 `alpha + beta + gamma = 1`，默认值 `[0.4, 0.3, 0.3]`。

**网络结构**：
- 输入层：社区特征 + 时段特征 + 媒体类型（one-hot）
- 共享底层：3层 MLP（256→128→64）
- 输出头：三个任务各一个输出层
- 激活函数：ReLU（隐藏层），Sigmoid（输出层）

#### 排期约束（数学描述）

```
目标：MAXIMIZE( SUM_t SUM_c(OTC[t,c] * x[t,c]) )

约束：
  (1) SUM_t SUM_c( cost[t,c] * x[t,c] ) <= Budget
  (2) x[t,c] in {0, 1}   # 0=不投放，1=投放
  (3) Frequency[c] <= MaxFreq   # 每人每天最多 MaxFreq 次
  (4) t_start <= t <= t_end   # 时间窗口
```

**求解方法**：FM 预测 + 贪心 heuristic（每次选边际 OTC/成本 最高的 `[t,c]` 组合）

**API 端点**：`POST /api/v2/agents/schedule-optimizer`

---

### 4.3 动态创意模块

**目标**：根据受众特征，实时生成/选择最合适的广告创意。

#### AIGC 文案生成

**Prompt 模板**：

```
你是一位专业的广告文案策划。请根据以下信息生成广告文案：

品牌：{brand}
产品：{product}
目标受众：{target_audience}
受众痛点：{pain_points}
品牌语调：{tone}  # 专业/活泼/温馨/高端
字数限制：{max_chars}

要求：
1. 标题不超过10个字
2. 正文不超过30个字
3. 包含明确的行动号召（CTA）
4. 不使用夸张或虚假宣传用语

输出格式：
JSON:
  'headline': '...'
  'body': '...'
  'cta': '...'
```

#### DCO（Dynamic Creative Optimization）算法

**多臂老虎机（Multi-Armed Bandit）**：

```
每个创意组合 = 一个「臂」
使用 UCB1 算法选择创意：

score[i] = avg_reward[i] + c * sqrt( ln(N) / n_i )

其中：
  avg_reward[i] = 创意i的历史点击率
  n_i = 创意i的展示次数
  N = 总展示次数
  c = 探索系数（默认1.0）
```

**API 端点**：`POST /api/v2/agents/creative-generator`

---

### 4.4 效果归因模块

**目标**：量化广告投放的实际效果（到店、转化）。

#### 跨端匹配算法

**匹配键构建**：

```python
# 曝光日志中的用户（匿名化）
exposure_user_id = hash(phone_last4 + device_id + community_id)

# 门禁记录中的用户（匿名化，与曝光使用相同hash盐值）
access_user_id = hash(phone_last4 + device_id + community_id)

# 匹配
matched = exposure_user_id == access_user_id
```

**重要**：hash 盐值每日轮换，且只保留7天内的匹配结果（隐私保护）。

#### 归因窗口函数

```
转化 = 1( 存在 access_record:
          exposure_user_id == access_user_id
          AND exposure_time <= access_time <= exposure_time + 7_days
       )
```

#### 核心指标计算公式

```
CAC = Total_Campaign_Cost / Number_of_Conversions

ROAS = Revenue_from_Conversions / Total_Campaign_Cost
       其中 Revenue = Conversion_Count × Average_Order_Value
```

**API 端点**：`POST /api/v2/agents/attribution`

---

### 4.5 RAG 知识库模块

**目标**：让 Agent 能查询行业知识、历史案例、竞品信息。

#### 检索流程代码

```python
from sentence_transformers import SentenceTransformer
import chromadb

class RAGRetriever:
    def __init__(self, collection_name: str):
        self.model = SentenceTransformer('text2vec-base-chinese')
        self.client = chromadb.PersistentClient(path='./chroma_db')
        self.collection = self.client.get_collection(collection_name)
    
    def retrieve(self, query: str, top_k: int = 5, filters: dict = None):
        # 1. 向量化查询
        query_embedding = self.model.encode(query)
        
        # 2. ChromaDB 检索
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=filters  # 可选：按 source/date 过滤
        )
        
        # 3. 组装上下文
        context = '\n\n'.join([
            f'[来源: {meta['source']}]\n{doc}'
            for doc, meta in zip(results['documents'][0], results['metadatas'][0])
        ])
        
        # 4. 注入 LLM prompt
        prompt = f'''
根据以下参考信息回答问题。如果参考信息不足以回答，请明确说明。

参考信息：
{context}

问题：{query}
'''
        return prompt
```

**API 端点**：`POST /api/v2/rag/query`

---

## 5. 用户使用流程

### 5.1 广告主投放流程（主要流程）

```
[1. 注册/登录]
      |
      ▼
[2. 创建投放计划]
   - 选择品牌/产品
   - 定义目标人群（年龄/收入/兴趣）
   - 设置预算和时间窗口
      |
      ▼
[3. AI 推荐点位]
   - 调用人群洞察 Agent
   - 返回推荐社区列表 + 预估 OTC
   - 用户调整选择
      |
      ▼
[4. AI 生成排期]
   - 调用智能排期 Agent
   - 返回最优媒体组合 + 时间安排
      |
      ▼
[5. AI 生成创意]
   - 调用动态创意 Agent
   - 生成多套创意方案
   - 用户选择/修改
      |
      ▼
[6. 确认并支付]
   - 系统生成合同（AI 辅助起草）
   - 在线支付（微信支付/银行转账）
      |
      ▼
[7. 投放执行]
   - 系统自动下发投放指令到媒体终端
   - 实时监控曝光数据
      |
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

## 6. AI Agent 编排逻辑与代码

### 6.1 统一编排 Agent（Orchestrator）

#### 三阶段工作流

```
用户请求
    |
    ▼
[规划阶段]  Orchestrator 分析请求，决定调用哪些 Agent
    |
    +---→ 需要人群分析？  ---> 调用 AudienceInsightAgent
    +---→ 需要排期优化？  ---> 调用 ScheduleOptimizerAgent
    +---→  need 创意生成？  ---> 调用 CreativeGeneratorAgent
    +---→  need 归因分析？  ---> 调用 AttributionAgent
    |
    ▼
[执行阶段]  各 Agent 并行或串行执行（根据依赖关系）
    |
    ▼
[反思阶段]  Orchestrator 检查执行结果
    |
    +---→ 结果满意？  ---> 返回用户
    +---→ 不满意？    ---> 调整参数，重新执行（最多 3 轮）
```

### 6.2 LangGraph 编排代码（完整示例）

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

class OrchestratorState(TypedDict):
    user_request: str
    plan: List[str]           # 需要调用的 Agent 列表
    agent_results: dict        # agent_name -> result
    reflection_count: int
    final_answer: Optional[str]


def planning_node(state: OrchestratorState) -> OrchestratorState:
    # 用 LLM 分析用户请求，生成调用计划
    llm = get_llm()
    response = llm.invoke(f'''
分析以下用户请求，决定需要调用哪些 Agent。
可选 Agent：audience_insight, schedule_optimizer, creative_generator, attribution
返回 JSON 数组，例如：['audience_insight', 'schedule_optimizer']

用户请求：{state['user_request']}
''')
    import json
    state['plan'] = json.loads(response.content)
    return state


def agent_executor_node(state: OrchestratorState) -> OrchestratorState:
    for agent_name in state['plan']:
        if agent_name == 'audience_insight':
            result = AudienceInsightAgent().run(state['user_request'])
        elif agent_name == 'schedule_optimizer':
            result = ScheduleOptimizerAgent().run(state['user_request'])
        # ... 其他 Agent
        state['agent_results'][agent_name] = result
    return state


def reflection_node(state: OrchestratorState) -> OrchestratorState:
    state['reflection_count'] += 1
    # 用 LLM 判断是否满意
    llm = get_llm()
    response = llm.invoke(f'''
检查以下 Agent 执行结果是否满意：
{state['agent_results']}

如果满意，输出 'SATISFIED'。
如果不满意，输出 'NOT_SATISFIED: <需要调整的Agent名> <调整建议>'。
''')
    if 'SATISFIED' in response.content:
        state['final_answer'] = synthesize_answer(state)
    return state


# 构建 LangGraph
workflow = StateGraph(OrchestratorState)

workflow.add_node('planning', planning_node)
workflow.add_node('execute', agent_executor_node)
workflow.add_node('reflect', reflection_node)

workflow.set_entry_point('planning')
workflow.add_edge('planning', 'execute')
workflow.add_edge('execute', 'reflect')

# 条件边：根据反思结果决定下一步
def should_continue(state):
    if state.get('final_answer'):
        return END
    if state['reflection_count'] >= 3:
        return END  # 强制结束
    return 'execute'  # 重新执行

workflow.add_conditional_edges('reflect', should_continue)

orchestrator = workflow.compile()
```

### 6.3 Agent 通信协议（JSON Schema）

#### Agent 输入 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentInput",
  "type": "object",
  "properties": {
    "input": {
      "type": "object",
      "properties": {
        "brand": { "type": "string" },
        "target": { "type": "string" },
        "budget": { "type": "number", "minimum": 0 }
      },
      "required": ["brand", "target"]
    },
    "context": {
      "type": "object",
      "properties": {
        "user_id": { "type": "string" },
        "session_id": { "type": "string" }
      }
    }
  },
  "required": ["input"]
}
```

#### Agent 输出 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentOutput",
  "type": "object",
  "properties": {
    "agent_name": { "type": "string" },
    "status": { "enum": ["success", "partial", "failed"] },
    "data": { "type": "object" },
    "reasoning": { "type": "string" },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
  },
  "required": ["agent_name", "status", "data"]
}
```

---

## 7. 数据模型（含 DDL）

### 7.1 核心数据库表（PostgreSQL DDL）

#### users（用户表）

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('advertiser', 'agent', 'admin', 'media_owner')) NOT NULL,
    company VARCHAR(255),
    phone VARCHAR(20),
    api_key VARCHAR(64) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
```

#### campaigns（投放计划表）

```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255) NOT NULL,
    product VARCHAR(255),
    budget DECIMAL(12,2) CHECK (budget >= 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_description TEXT,
    status VARCHAR(20) CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled')) DEFAULT 'draft',
    estimated_otc DECIMAL(12,2),
    actual_cost DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_date_range CHECK (end_date >= start_date)
);

CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);
```

#### creatives（创意素材表）

```sql
CREATE TABLE creatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    type VARCHAR(20) CHECK (type IN ('image', 'text', 'video', 'html5')) NOT NULL,
    headline VARCHAR(50),
    body TEXT,
    cta_text VARCHAR(30),
    image_url VARCHAR(512),
    content JSONB,
    performance_score FLOAT CHECK (performance_score >= 0 AND performance_score <= 1),
    ab_test_group VARCHAR(20),
    impression_count INT DEFAULT 0,
    click_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_creatives_campaign_id ON creatives(campaign_id);
```

#### otc_logs（OTC 归因日志表）

```sql
CREATE TABLE otc_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    community_id VARCHAR(64) NOT NULL,
    user_id_hash VARCHAR(64) NOT NULL,
    touch_time TIMESTAMP NOT NULL,
    touch_location VARCHAR(255),
    media_type VARCHAR(20),
    convert_time TIMESTAMP,
    otc_value FLOAT,
    is_matched BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_otc_campaign_id ON otc_logs(campaign_id);
CREATE INDEX idx_otc_user_hash ON otc_logs(user_id_hash);
CREATE INDEX idx_otc_touch_time ON otc_logs(touch_time);
CREATE INDEX idx_otc_matched ON otc_logs(is_matched) WHERE is_matched = TRUE;
```

#### inventory（媒体库存表）

```sql
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id VARCHAR(64) NOT NULL,
    community_name VARCHAR(255) NOT NULL,
    media_type VARCHAR(20) CHECK (media_type IN ('door_lightbox', 'gate', 'app', 'led')) NOT NULL,
    device_id VARCHAR(64),
    location_desc VARCHAR(255),
    daily_capacity INT,
    price_per_day DECIMAL(8,2),
    is_active BOOLEAN DEFAULT TRUE,
    geom GEOMETRY(Point, 4326),  -- PostGIS 坐标
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_inventory_community ON inventory(community_id);
CREATE INDEX idx_inventory_media_type ON inventory(media_type);
CREATE INDEX idx_inventory_geom ON inventory USING GIST(geom);
```

### 7.2 5V 数据层接口（完整代码）

```python
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional


class DataProvider(ABC):
    """5V 数据层统一接口"""

    @abstractmethod
    def query(self, filters: Dict) -> pd.DataFrame:
        """根据过滤条件查询数据
        参数：
            filters: 字典，键为字段名，值为过滤条件
                     例如：{'city': '深圳', 'min_age': 30}
        返回：
            符合条件的 DataFrame
        """
        pass

    @abstractmethod
    def get_coverage(self, city: str) -> float:
        """返回数据在城市中的覆盖率（0.0-1.0）"""
        pass

    @abstractmethod
    def get_stats(self, community_id: str) -> Dict:
        """返回单个社区的数据统计摘要"""
        pass


class V4AccessDataProvider(DataProvider):
    """V4 门禁数据 Provider（核心实现）"""

    def __init__(self, db_connection):
        self.conn = db_connection

    def query(self, filters: Dict) -> pd.DataFrame:
        sql = '''
        SELECT community_id, user_id_hash, access_time, access_type
        FROM v4_access_logs
        WHERE 1=1
        
        params = []
        if 'community_id' in filters:
            sql += ' AND community_id = %s'
            params.append(filters['community_id'])
        if 'start_date' in filters:
            sql += ' AND access_time >= %s'
            params.append(filters['start_date'])
        # ... 其他过滤条件
        return pd.read_sql(sql, self.conn, params=params)

    def get_coverage(self, city: str) -> float:
        # 查询该城市已部署门禁的小区占比
        sql = '''
        SELECT COUNT(DISTINCT community_id) * 1.0 / (SELECT COUNT(*) FROM communities WHERE city = %s)
        FROM v4_access_logs vl
        JOIN communities c ON vl.community_id = c.id
        WHERE c.city = %s
        '''
        cursor = self.conn.cursor()
        cursor.execute(sql, (city, city))
        return cursor.fetchone()[0]

    def get_stats(self, community_id: str) -> Dict:
        sql = '''
        SELECT 
            COUNT(*) as total_access,
            COUNT(DISTINCT user_id_hash) as unique_users,
            AVG(EXTRACT(HOUR FROM access_time)) as avg_hour
        FROM v4_access_logs
        WHERE community_id = %s
        AND access_time >= NOW() - INTERVAL '30 days'
        '''
        cursor = self.conn.cursor()
        cursor.execute(sql, (community_id,))
        row = cursor.fetchone()
        return {
            'total_access_30d': row[0],
            'unique_users_30d': row[1],
            'avg_access_hour': row[2]
        }
```

---

## 8. API 完整规范与客户端示例

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

#### Python 客户端示例

```python
import requests
import json

BASE_URL = 'https://api.aiadplacer.com/api/v2'
API_KEY = 'your_api_key_here'

headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}


def invoke_audience_insight(brand: str, target: str, cities: list, budget: float):
    url = f'{BASE_URL}/agents/audience-insight/invoke'
    payload = {
        'input': {
            'brand': brand,
            'target': target,
            'cities': cities,
            'budget': budget
        },
        'context': {
            'user_id': 'user_123'
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def invoke_schedule_optimizer(campaign_id: str, budget: float, start_date: str, end_date: str):
    url = f'{BASE_URL}/agents/schedule-optimizer/invoke'
    payload = {
        'input': {
            'campaign_id': campaign_id,
            'budget': budget,
            'start_date': start_date,
            'end_date': end_date,
            'media_types': ['gate', 'door_lightbox']
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    # 轮询任务状态
    task_id = response.json()['task_id']
    return poll_task(task_id)


def poll_task(task_id: str, max_wait: int = 60):
    import time
    url = f'{BASE_URL}/tasks/{task_id}'
    for _ in range(max_wait // 3):
        resp = requests.get(url, headers=headers)
        data = resp.json()
        if data['status'] in ('completed', 'failed'):
            return data
        time.sleep(3)
    return {'status': 'timeout'}


if __name__ == '__main__':
    # 示例：调用人群洞察
    result = invoke_audience_insight(
        brand="宝马",
        target="35-45岁，家庭年收入>50万，有车",
        cities=["深圳", "广州"],
        budget=500000.0
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

#### curl 示例

```bash
# 调用人群洞察 Agent
curl -X POST 'https://api.aiadplacer.com/api/v2/agents/audience-insight/invoke' \
  -H 'X-API-Key: your_api_key' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": {
      "brand": "宝马",
      "target": "35-45岁，高收入",
      "cities": ["深圳"],
      "budget": 500000
    }
  }'

# 查询任务状态
curl 'https://api.aiadplacer.com/api/v2/tasks/{task_id}' \
  -H 'X-API-Key: your_api_key'
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

**MCP Server 实现**（FastAPI）：

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

class MCPToolInvokeRequest(BaseModel):
    tool_name: str
    parameters: dict


@app.post('/api/v2/mcp/tools/invoke')
async def invoke_mcp_tool(req: MCPToolInvokeRequest):
    if req.tool_name == 'search_community':
        result = search_community(**req.parameters)
    elif req.tool_name == 'estimate_otc':
        result = estimate_otc(**req.parameters)
    else:
        raise HTTPException(404, 'Tool not found')
    
    return {
        'tool_name': req.tool_name,
        'result': result,
        'status': 'success'
    }
```

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
                             |
              ┌──────────────┼──────────────┐
              |              |              |
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
       │ FastAPI #1  │ │ FastAPI #2 │ │ FastAPI #3│
       │ (workers)   │ │ (workers)  │ │ (workers) │
       └──────┬─────┘ └─────┬──────┘ └────┬─────┘
              |              |              |
              └──────────────┼──────────────┘
                             |
              ┌──────────────┼──────────────┐
              |              |              |
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

## 13. 附录：术语表与重新实现指南

### 13.1 术语表

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
| FM | Factorization Machines | 因子分解机，推荐算法 |
| UCB1 | Upper Confidence Bound 1 | 多臂老虎机算法 |

### 13.2 重新实现指南（给 AI 开发者的说明）

如果您是一位 AI 开发者，希望基于本文档重新实现一个类似的系统，以下是建议的技术路线：

#### A. 最小可行产品（MVP）功能清单

1. 用户注册/登录（可以用 Auth0 或 Supabase Auth）
2. 社区数据上传 + 管理（CSV 导入即可）
3. 基于规则的推荐（先不用 AI，用 SQL 查询 + 规则引擎）
4. 投放计划创建 + 管理
5. 基础报告（Excel 导出）

#### B. 逐步添加 AI 能力

1. 先接一个 LLM（OpenAI API 或国内大模型 API）
2. 实现 RAG：上传几份行业报告，让系统能回答简单问题
3. 实现第一个 Agent（人群洞察）：用 LLM 分析上传的社区数据
4. 添加更多 Agent，用 LangGraph 编排
5. 实现 MCP 接口，让外部 AI 能调用你的系统

#### C. 关键开源组件推荐

| 功能 | 推荐组件 |
|------|----------|
| API 框架 | FastAPI（Python）/ Express（Node.js） |
| Agent 编排 | LangGraph / AutoGen / CrewAI |
| 向量数据库 | ChromaDB（本地）/ Pinecone（云端） |
| 嵌入模型 | text2vec-base-chinese（中文）/ all-MiniLM-L6-v2（英文） |
| 数据库 | PostgreSQL + PostGIS（地理数据） |
| 任务队列 | Celery + Redis |
| 前端 | React + Tailwind CSS |

#### D. 数据获取建议

- **社区数据**：可以从公开数据平台（如高德地图 POI、链家房价数据）获取
- **门禁数据**：这是独家数据，重新实现时可以用「到店打卡」或「WiFi 连接记录」替代
- **户外广告标准**：参考 IAB 和 CCSA 的公开标准文档

---

*文档结束 — 如需补充任何章节，请联系产品团队。*