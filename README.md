# 🎯 AIAdPlacer — 户外广告行业的AI Copilot工具箱

核心价值：
- 帮广告主做投放决策（AI分析+推荐）
- 帮媒体主管理库存（AI排期+定价）
- 帮代理商提升效率（AI报告+竞品监控）

落地路径：
v1 → 成为Tom的私人工具（不求商业化，先验证）

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
  🔗 对接文档：<a href="http://47.253.159.62:8888/">http://47.253.159.62:8888</a>
</p>

---

## 🔥 为什么这个项目值得关注？

> **pDOOH（程序化数字户外广告）是全球广告科技的下一个万亿级赛道，但目前尚无一个开源、完整、可落地的 AI Native 系统。**

AIAdPlacer 填补了这个空白：

- ✅ **全球首个** AI Native pDOOH 开源系统
- ✅ 完整实现 **5V 数据模型**（人口 / 消费 / 社区 / 门禁 / 行为）
- ✅ **A2A 接口**（AI-to-AI），其他 AI Agent 可直接调用投放能力
- ✅ 对接**腾讯地图 LBS** + **青柠**社区数据底座
- ✅ 内置 **LLM Agent 编排**（人群洞察 → 智能排期 → 动态创意 → 效果归因）
- ✅ **符合 T/CCSA 738—2025 行业标准**（程序化户外广告投放曝光测量技术要求）

> 📋 **行业标准对齐**：系统曝光测量逻辑已对标中国广告协会 + 中国通信标准化协会联合发布的行业标准，涵盖流动曝光、驻留曝光、曝光乘数、OTC 概率等核心指标。详见 [`docs/industry_standard_terms_and_guide.md`](docs/industry_standard_terms_and_guide.md)

---

## 🔄 DOOH → pDOOH：户外广告的程序化革命

> **传统户外广告（DOOH）正在经历从「人工排期」到「程序化交易」的根本性转变。**

下图直观展示了两种投放模式的本质差异：

<p align="center">
  <img src="docs/pdooh-transformation.png" alt="DOOH → pDOOH 转变" width="900" />
</p>

### 传统投放模式 vs 程序化投放模式

| 维度 | 传统 DOOH | 程序化 pDOOH（本系统） |
|------|----------|------------------------|
| **购买目标** | 位置、周期、价格（固定） | Impression、触发条件、CPM（动态） |
| **决策方式** | 人工谈判 + Excel 排期 | AI 算法自动竞价 + 实时匹配 |
| **交易链路** | 品牌/媒介代理 → 媒体 → 曝光 → 受众 | DSP ↔ SSP 实时数据交换，按需定向 |
| **受众触达** | 广撒网，无法精确 | 基于广告主需求，对目标受众精准曝光 |
| **效率** | 周级排期，人工审核 | 毫秒级响应，自动化全流程 |

### 本系统的定位

AIAdPlacer 正是这张图中**程序化投放模式**的完整落地实现：

- **DSP（需求方平台）**：`/api/v2/pdooh/*` + `Tom Agent(5003)` — 广告主侧的智能投放引擎
- **SSP（供应方平台）**：`/api/v2/db/*` + `qinlin_local.db` — 媒体主侧的资源管理与库存调度
- **实时竞价核心**：`ROI Agent(5004)` + `竞品Agent(5005)` — 自动化价格优化与竞争情报
- **数据交换协议**：**A2A / MCP 接口**（25 个工具）— 让其他 AI Agent 直接调用投放能力

> 💡 **一句话总结**：传统模式下，广告主买的是「一块屏幕 × N 天」；pDOOH 模式下，广告主买的是「对目标受众的 N 次精准曝光」。AIAdPlacer 就是连接这两端的桥梁。

---

## 🌍 竞争格局：六大 pDOOH 平台对标

理解了 pDOOH 的革命性后，自然要问：**这个赛道里已经有哪些玩家？我们凭什么立足？** 下面把全球主流 pDOOH 平台与我们的 AIAdPlacer 做一次横向对标。

| 维度 | Vistar Media | VIOOH | 分众传媒 | Broadsign / Hivestack | JCDecaux 德高 | **我们 · AIAdPlacer** |
|------|------|------|------|------|------|------|
| **核心资产 / 技术栈** | 程序化交易技术栈（SSP+DSP） | 媒体资源程序化平台 | 高端网络电梯媒体（自有） | 广告服务器 + 程序化技术中台 | 交通枢纽媒体（地铁/机场/街道设施） | **AI 中台技术栈 + AI 深度投放优化层** |
| **第三方媒体接入** | ✅ 强（第三方媒体聚合） | ⚠️ 弱（媒体资源独占，自有为主） | ❌ 无（纯自有网络） | ✅ 强（中立技术平台） | ⚠️ 中（自有为主 + 部分第三方） | ✅ 开放（可接入任意媒体源） |
| **主要市场** | 北美 + 欧洲 | 欧洲 + 部分亚太 | 中国大陆 | 全球 | 全球 | 中国（可扩展全球） |
| **壁垒** | 先发 + 客户关系 | 媒体资源独占 | 场景垄断 + 品牌客户 | 技术 + 生态位 | 场景资源 + 品牌 | **AI 算法 + 开放生态** |
| **技术 + 生态位** | 中 | 中 | 高 | 高 | 中 | **高** |
| **天花板** | 高 | 高 | 极高 | 中 | 高 | **高（AI 中台潜力极高）** |

### 平台差异化解读

- **Vistar Media** — 北美程序化 DOOH 的**先发者**，靠先发优势 + 深厚的媒体客户关系建立壁垒，技术栈偏「交易管道」本身。市场集中在北美 + 欧洲，生态位偏中立但天花板受限于北美媒体存量。

- **VIOOH** — 由 JCDecaux 分拆出的程序化平台，**壁垒来自媒体资源独占**（背后是德高的自有屏幕）。这种「资源即护城河」模式在欧洲 + 部分亚太很强，但第三方媒体接入弱，扩张受自有资源天花板约束。

- **分众传媒** — 中国**电梯媒体的绝对垄断者**，核心资产是「高端网络电梯媒体」这一封闭自有网络。壁垒 = 场景垄断 + 顶级品牌客户，技术 + 生态位高、天花板极高。短板是：纯自有网络、几乎无第三方接入、AI 优化层薄。

- **Broadsign / Hivestack** — **技术中台型**玩家，提供广告服务器 + 程序化能力给全球各类媒体主，靠「技术 + 生态位」立身，市场覆盖全球。天花板中等——它卖的是「水电煤」基础设施，而非直接触达广告主的投放价值。

- **JCDecaux 德高** — 全球**交通枢纽媒体霸主**（地铁 / 机场 / 街道设施），场景资源 + 品牌壁垒强，市场全球分布。技术 + 生态位中等，程序化能力正在补课。

### 我们的差异化卡位

> **别人卖「屏幕」，我们卖「算法 + 投放优化能力」。**

1. **唯一以 AI 中台为底座的开放平台** — 我们不与分众、德高抢「屏幕资源」，而是把 **AI 中台技术栈 + 深度投放优化层**（投放优化 + 创意生成 + 效果预测）作为核心资产，可**接入任意媒体源**，不被单一资源方绑架。
2. **完整的 AI 深度投放优化闭环** — 投放优化层（Tom / ROI / 竞品 Agent）+ 创意生成（DCO 引擎）+ 效果预测（ROI Agent）三者打通，是 Vistar / VIOOH / 德高都尚未集成的端到端能力。
3. **开放生态位 = 极高潜力天花板** — 技术 + 生态位评「高」，且因 AI 中台可横向赋能电梯、地铁、公交、社区、机场全场景，天花板对标分众「极高」量级，却不受单一场景垄断限制。

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────┐
│                 前端展示层                        │
│  demo.html（腾讯地图可视化）· bmn-frontend/     │
│  bus-demo.html（公交线路热力图）                │
│  web/index.html（AI Copilot 管理台）            │
└──────────────────┬──────────────────────────────┘
                     │ REST / WebSocket / MCP
┌─────────────────────────────────────────────────────┐
│            多端口微服务层 (Ports 5002-5006)         │
│                                                       │
│  Port 5002: FastAPI 主服务                          │
│    /api/v2/pdooh/*  ·  /api/v2/agents/*           │
│    /api/v2/rag/*   ·  /api/v2/mcp/*  (A2A)      │
│    /api/v2/bus/*    ·  /api/v2/dashboard/*      │
│                                                       │
│  Port 5003: Tom Agent (CPM 计算 + 投放方案生成)    │
│  Port 5004: ROI Agent (三场景 ROI 计算)            │
│  Port 5005: 竞品Agent (竞品监控 + 市场情报)        │
│  Port 5006: BabyAGI (任务自动化编排引擎) ⭐ 新增   │
└──────────────────┬──────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│                  AI 能力层                           │
│  LangGraph Agent 编排  ·  ChromaDB 向量检索       │
│  BabyAGI 任务队列  ·  Ollama 本地 LLM           │
└──────────────────┬──────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────┐
│                  数据层                              │
│  PostgreSQL (pdooh + ai_adplacer + qinlin_local)  │
│  Redis · ChromaDB · SQLite (点位数据)             │
└─────────────────────────────────────────────────────┘
```

---

## 🗃️ 核心数据模型（青柠 5V 底座）

| V层 | 数据维度 | 表中字段 | 业务价值 |
|------|----------|----------|----------|
| **V1** 人口属性 | 年龄/性别/学历/收入 | `person_anchor` | 基础人群定向 |
| **V2** 消费偏好 | 母婴/汽车/理财 DMP标签 | `person_dmp_tags` | 精准兴趣投放 |
| **V3** 社区属性 | 楼盘/户型/房价/入住率 | `screen.extended_props` | 社区价值评估 |
| **V4** 门禁动作 ⭐ | 扫码/刷脸/刷卡记录 | `spatial_trajectory` | **独家优势**：真实到店证据 |
| **V5** 线上行为 | APP使用/浏览轨迹 | `person_dmp_tags (extended)` | 跨屏人群扩展 |

> 💡 **V4 门禁数据**是青柠的核心壁垒——每次「开门」都是一次真实到店验证，任何其他 pDOOH 系统都不具备这个数据维度。

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

### 🚇 subway-pDOOH 子系统（地铁程序化投放）⭐ 新增

基于**德高中国《地铁程序化数字户外白皮书》** 权威方法论，为 AIAdPlacer 新增地铁场景程序化投放模块：

#### 核心算法能力（源自白皮书实践）

| 算法/能力 | 来源 | 对系统架构的提升 |
|-----------|------|----------------|
| **MAM 地铁受众测量系统** | 德高集团主导，CCSA + CAA 联合发布 T/CCSA 738-2025 / T/CAAAD 006-2025 | 填补国内 pDOOH 曝光测量标准空白，可直接作为 `Placement.impressions` 的权威计算依据 |
| **TA 标签定向算法** | 整合 CRM + 第三方 DMP，提炼人口统计/消费心理/行为偏好标签 | 升级 `pdooh_query_persons` 的受众匹配精度 |
| **POI 场景定向算法** | LBS + POI 邻近关系计算，超本地化触达 | 新增 POI 定向过滤参数到 `pdooh_query_screens` |
| **外部数据联动触发** | 天气/实时位置/消费动态 → DCO 动态创意切换 | 升级 `pdooh_submit_creative` 支持 DCO 规则引擎 |
| **跨渠道再营销定向** | pDOOH 曝光人群包 → 线上 Retargeting | 新增跨渠道人群包导出 API |
| **DCO 动态创意优化** | 实时数据触发素材切换（气温触发/时段触发/客流触发） | 新增 `pdooh_dco_trigger` MCP 工具 |

#### 白皮书核心洞察（可直接落地为系统功能）

1. **曝光量测算模型**：结合车站人数、客流动线、媒体尺寸、广告播放时长 → 算出 Impression
   - ✅ 已对齐：系统已符合 T/CCSA 738-2025 行业标准
2. **POI 场景定向**：基于受众与 POI（零售店/场馆/枢纽/写字楼）邻近关系筛选点位
   - 🔧 待实现：在 `db_api.py` 中新增 POI 过滤参数
3. **跨渠道再营销**：pDOOH 曝光 → 构建专属人群包 → 线上二次触达
   - 🔧 待实现：新增 `/api/v2/dashboard/audience-retarget` 端点
4. **DCO 动态创意**：气温≥33℃ 自动切换高温版素材（脉动案例）；15℃以下播轻薄羽绒服（优衣库案例）
   - 🔧 待实现：新增 `creative_rules` 表 + DCO 引擎

#### 地铁板块方案文档

完整技术方案请查阅：**`docs/subway-solution.md`**（含 MAM 系统集成方案、POI 定向算法、DCO 规则引擎设计）

---

### 🖥️ 智能屏资源子系统（Smart Screen L9）⭐ 新增

基于真实数据「智能屏L9.xls」（sheet「媒体列表」，**9802 行（含表头 1 行）× 12 列**，真实媒体数据 9801 行），为 AIAdPlacer 新增独立的**智能屏资源评估子系统**，采用**四层架构（输入层 / 关联层 / 算法层 / 产出层）** 落地小区级/点位点位的 39 维价值指标。

> 设计文档：[`docs/smart-screen-l9.md`](docs/smart-screen-l9.md)（含完整建表 SQL、19 算法目录、39 指标定义、ER/时序/类图）

#### 四层架构

| 层 | 中文 | 内容 | 物理落库 |
|----|------|------|----------|
| **输入层** | 4 孤岛 | 媒体列表（真实 xls）+ 小区 / 设备 / 投放 / 销售（派生占位） | `t_media_l9` `t_community` `t_device` `t_delivery` `t_sales` |
| **关联层** | 5 纽带 | 户数/入住率/楼栋/设备/投放 JOIN 成小区级宽表 | `t_community_wide`（13 业务字段） |
| **算法层** | 19 算法 | 人口覆盖/质量评分/效果预测/价值分析 4 大类算法注册位 | `t_algorithm`（19 行，`status='registered'`） |
| **产出层** | 39 指标 7 大类 | A 人口覆盖(5) / B 质量评分(5) / C 效果预测(4) / D 价值分析(5) / E 画像标签(5) / F 空间价值(4) / G 行业适配(11) | `t_poi_indicators` |

- **独立库隔离**：落库于 `backend/data/smart_screen_l9.db`（与 `qinlin_local.db` 物理隔离），DAO 走 `ss_dao.py`，不复用主库 `db_dao`。
- **数据源单一事实来源**：`schema_constants.py` 集中定义 4 层 / 19 算法 / 39 指标，全模块引用，禁止硬编码。
- **示意算法占位**：19 算法仅注册元数据；39 指标由 `indicator_formulas.py` 的启发式函数生成（注释标注「示意算法，待替换为真实模型」），GPS 缺失下空间类（F）以占位公式生成。

#### 构建命令（一键生成 DB，开箱即用）

```bash
cd backend
# 创建隔离 venv 并安装构建依赖（xlrd 必须锁 <2.0 才能读 .xls）
python -m venv .venv_ss
.\.venv_ss\Scripts\pip.exe install pandas xlrd==1.2.0 fastapi pydantic httpx pytest

# 构建智能屏子系统库
.\.venv_ss\Scripts\python.exe -m app.smart_screen.cli ^
    --xls "D:/BaiduNetdiskDownload/Other/皓邻/智能屏L9.xls"
```

> 构建幂等（`DROP` + `CREATE`），重跑可重建；生成的 `smart_screen_l9.db` 已提交仓库，可开箱即用。

#### API 端点（前缀 `/api/v2/smart-screen`）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v2/smart-screen/tables` | 子系统表清单 + 行数 |
| GET | `/api/v2/smart-screen/communities` | 小区级宽表（可按 省/市/区 筛选） |
| GET | `/api/v2/smart-screen/indicators/{community_id}` | 某小区 39 指标 |
| GET | `/api/v2/smart-screen/media` | 媒体列表（筛选 + 分页） |
| GET | `/api/v2/smart-screen/stats` | 子系统整体统计 |
| GET | `/api/v2/smart-screen/algorithms` | 19 算法注册表 |

响应体统一 `{success, data/error, code, total?}`（与 `db_api.py` 风格一致）。

#### 数据规模

| 维度 | 规模 |
|------|------|
| 媒体点（`t_media_l9`） | **9,801** 行（xls「媒体列表」共 9,802 行，含表头 1 行） |
| 小区（`t_community`） | 由网点名称聚合派生 |
| 设备（`t_device`） | 由 MAC 去重派生 |
| 指标（`t_poi_indicators`） | 小区级 39 指标全覆盖 |
| 算法（`t_algorithm`） | 19 个 |

#### ROI 预估算法真实化

将 `roi_estimate` 由「示意占位公式」升级为**可解释的真实 ROI 模型**（对应 `ALG_V_ROI`，算法目录 `formula_hint` 已同步为单一事实来源）。重算通过新增 CLI 子命令幂等刷新：

```bash
cd backend
# 幂等重算 39 指标（一次刷新 roi_estimate + value_index 两列）
.\.ss_venv\Scripts\python.exe -m app.smart_screen.cli recompute-indicators
```

- **业务定义**：衡量单个小区智能屏投放的「投入产出比」，输出 0–100 的 ROI 指数（盈亏平衡→50，越赚越接近 100，越亏越接近 0），供 `value_index` 价值指数聚合使用，辅助选点决策。

- **公式（成本 / 收益 / ROI / 指数 clip）**：

  ```
  日触达 reach   = daily_reach(row)            # 复用既有函数：household_count × occupancy_rate × 2.1
  成本   cost    = CPM × reach / 1000          # 等价于单屏日投放成本 access_lightbox_price
  收益   revenue = reach × CVR × AOV
  真实ROI        = (revenue − cost) / cost
  ROI指数        = clip(revenue−cost)/cost × 50 + 50 , 0, 100)   # 盈亏平衡→50，≥100%→100，≤−100%→0
  ```

- **常量取值与来源**（P0 采用社区梯媒统一常量，不按社区差异化；差异化留待 P1）：

  | 常量 | 取值 | 含义 | 来源 |
  |------|------|------|------|
  | `CVR` | `0.008` | 转化率（到店/扫码率） | 社区梯媒行业经验区间 0.5%–2% 取中值 |
  | `AOV` | `80.0` | 客单价（元） | 社区周边消费行业经验区间 50–120 元取中值 |

- **与 `value_index` 的关系**：`value_index = (cost_performance + roi_estimate + effect_predict) / 3`，`roi_estimate` 是其中一项；重算时 `generate_indicators` 一次性刷新两列，调用方无需改动。`roi_estimate` 签名为 `roi_estimate(row: dict) -> float`，与旧版本保持一致（仅替换函数体 + 新增模块级常量）。

- **验收要点**：
  1. `roi_estimate(row)` 返回值恒在 `[0, 100]` 闭区间，无非有限值（NaN/Inf）。
  2. 中值用例（`reach=210, cost=80`）→ 指数 ≈ `84.0`；收益远高于成本时封顶 `100.0`；触达极小/成本极高时触底 `0.0`。
  3. `t_poi_indicators` 全量重算后分布合理（非空、非全 0/全 100、方差合理），`value_index` 无 NaN/越界。
  4. 纯函数单测 `tests/test_roi_estimate.py` 覆盖上述三档 + 边界 + 常量口径，可独立运行（`pytest tests/test_roi_estimate.py`）。

---

### 🍋 青柠智能助手（Qinglin Assistant）⭐ 新增

将「青柠」品牌智能对话能力以**垂直切片**方式接入 AIAdPlacer，挂载于 `/api/v2/assistant`，复用既有 LLM 兼容抽象层（默认本地 Ollama，`.env` 可切 OpenAI 兼容云端）。

**核心能力（垂直切片）**

| 能力档 | 行为 | 数据真实性 |
|--------|------|-----------|
| 知识库真查 | 门禁 / 单元门 / 道闸 / 客户等真实点位查询 | ✅ 走真实主库 `qinlin_local.db`，返回可核对真实数字（如全国门禁 66,308 / 广州 2,174） |
| 演示态操作 | 报备 / 锁点 / 导点 | 🟡 真实链路 + 模拟落库，响应体带 `demo:true` 并标注「演示态」+ 编号 `DEMO-*` |
| 纯对话 | 通用问答（依赖 LLM） | ⚠️ LLM 不可用（Ollama 关闭）时**明确返回 HTTP 503 + `LLM_UNAVAILABLE`**，绝不静默 mock 假文案 |

**四角色 RBAC**：`sale`（销售）/ `media`（媒介）/ `engineer`（工程）/ `developer`（商业开发）。越权动作（如 sale 执行 shell）直接拦截，不访问底层数据。

**端点**

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v2/assistant/health` | 健康检查（DB 可达性 + LLM 可用性） |
| GET | `/api/v2/assistant/roles` | 四角色能力清单 |
| POST | `/api/v2/assistant/chat` | 对话入口（意图识别 → RBAC → 工具编排 → 记忆持久化） |

**验收**：回归测试 `backend/tests/test_qinglin_assistant.py` 覆盖健康 / 角色 / 真查 / 503 / RBAC / 演示态全链路，**8/8 通过**。设计文档见 [`docs/incremental_design_qinglin_assistant.md`](docs/incremental_design_qinglin_assistant.md)。

---

### 🔒 青柠 Booking 真实锁位模块（P0）⭐ 新增

面向社区媒体「真实锁位 / 预占 / 排期」的库存交易闭环，已上线 `/api/v2/bookings`。品牌统一「青柠」、代码标识 `qinglin`，磁盘库沿用 `qinlin_local.db`（表名保持原样不动）。

**四层超卖防护（库存交易最后防线）**

| 层 | 防护 | 实现 |
|----|------|------|
| ① 接口预检 | 下单前占位可用性校验 | `booking_service.check_availability` |
| ② 分布式锁 | Redis `SET NX PX` 防并发抢占同一点位 | `redis` 锁（带自动过期） |
| ③ 悲观锁 | 事务内 `SELECT ... FOR UPDATE ORDER BY id` 串行化写入 | `async SQLAlchemy` |
| ④ 排他约束 | 绕过应用直插重叠 → 触发 `23P01` | DB 层 `EXCLUDE USING gist` 硬约束 |

**核心模型**（`backend/app/models/booking.py`）：`Booking`（UUID 主键 · `booking_no` 唯一 · 7 态状态机 · `idempotency_key` 幂等）、`LockTierConfig`（五档锁位参数 A++ / A+ / A / B / C）、`MediaLevelRule`（媒体类型 × 城市 → 锁位级别，可配置派生，**无 level 列**）。

**端点**（前缀 `/api/v2/bookings`，注意带尾斜杠）：

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v2/bookings/precheck/` | 锁位预检（可用性 + 冲突） |
| POST | `/api/v2/bookings/` | 创建锁位（四层防护 + 幂等） |
| POST | `/api/v2/bookings/{no}/extend/` | 延长锁位 |
| POST | `/api/v2/bookings/{no}/release/` | 释放锁位 |
| POST | `/api/v2/bookings/{no}/cancel/` | 取消锁位 |
| POST | `/api/v2/bookings/{no}/install/` | 上刊确认 |
| GET | `/api/v2/bookings/` | 锁位列表（筛选） |
| GET | `/api/v2/bookings/{no}/` | 锁位详情 |
| GET | `/api/v2/bookings/point/{id}/timeline/` | 单点位锁位时间线 |

**锁位到期释放**：`backend/app/tasks/booking_release.py` 的 `release_expired_bookings()` 扫描 `LOCKED` 且 `expire_at` 过期记录 → 置 `EXPIRED` + 释放 Redis 锁；`app/main.py` 启动时拉起调度器。

**验收**：并发测试 `backend/tests/test_booking_ct.py`（并发同点位仅 1 成功 / 到期释放 / 幂等 / 直插 23P01 / 无脏数据 / 多点位全成功）+ `backend/tests/test_etl_media.py`（level 派生 + ETL 幂等），**10/10 通过**；端到端真跑验证 `/docs` 注册 8 条 booking 路由、创建 / 查询 / 重叠(409) / 释放全链路 OK。需求文档见 [`docs/prd_qinglin_booking_p0.md`](docs/prd_qinglin_booking_p0.md)、设计文档见 [`docs/design_qinglin_booking_p0.md`](docs/design_qinglin_booking_p0.md)。

---

### 📺 创视媒体资源子系统（Chuangshi）⭐ 新增

将「创视广东资源明细」清洗为独立业务库 + 单文件售卖模版 + CPM 数据架构，支撑社区写字楼媒体的可售库存管理与定价测算。

**数据源**：`创视广东资源明细-0624.xlsx`（1 个明细 sheet，含标题行 + 元信息行 + 真实表头 12 列）；两个媒体形式 = **大屏 239 屏** + **电梯LCD屏 3725 屏**，**点位 = 单屏设备，合计 3964**（与标题「点位总数 3964」吻合，≠ 位置行 2724）；广东省 12 城市、513 栋楼、项目类型 100% 写字楼。

**库结构**（`backend/data/chuangshi_local.db`，仿 `qinlin_local.db` 命名，与青柠库物理并列独立）：

| 对象 | 说明 |
|------|------|
| `chuangshi_points` | 点位 SSOT，单屏设备级 3964 行（省/市/区县/楼宇编码/项目/楼层/等候厅/媒体形式/屏数） |
| `media_form_pricing` | CPM 定价表（大屏 / 电梯LCD屏 两行，刊例价 + 单屏日均曝光，默认 NULL 待补） |
| 视图 `v_point_cpm` | 单点位 CPM 计算（屏数 / 周曝光 / 周刊例价 / CPM） |
| 视图 `v_stats_by_city` · `v_stats_by_media_form` · `v_stats_by_city_media` | 统计聚合（屏数·楼宇数·覆盖城市等） |

**CPM 公式（架构就绪，真实数值留空待补，不编造）**：`CPM(周) = 刊例价(元/周/屏) × 1000 ÷ (单屏日均曝光 × 7)`（屏数在分子分母抵消，按媒体形式算费率）。

**单文件售卖模版**（`chuangshi_sales_template.html`，双击即开，离线可用）：左侧搜索 / 筛选（城市·区县·楼宇·媒体形式）+ 可编辑 CPM 定价面板（localStorage 持久化）+ 右侧 KPI / 统计看板（按城市 / 媒体形式纯 CSS 柱状图）+ 可售清单 CSV 导出。已用 jsdom 无头真跑验证：全新打开 0 崩溃、搜索 / 筛选 / 填价即时算 CPM。

**构建命令（一键生成，幂等）**：

```bash
cd backend
.\venv\Scripts\python.exe scripts/build_chuangshi_db.py
# → 生成 chuangshi_local.db + chuangshi_data.json（内嵌 HTML 的数据 bundle）
```

**验收**：db 行数 / 视图独立核验通过（大屏 = 239 / 电梯LCD屏 = 3725 / 点位 = 3964）；CPM 视图正确返回 NULL（未编造数据）。架构文档见 [`docs/chuangshi_data_architecture.md`](docs/chuangshi_data_architecture.md)。

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
│   │   ├── bmn/               # BMN 品牌增长系统
│   │   ├── routers/bookings.py # ⭐ 青柠 Booking 真实锁位模块（P0）
│   │   ├── models/booking.py   # Booking / LockTierConfig / MediaLevelRule
│   │   ├── services/booking_service.py # 四层超卖防护 + 幂等创建
│   │   └── tasks/booking_release.py     # 锁位到期释放调度
|   ├── bus-demo.html           # ⭐ bus-pDOOH 演示页面
│   ├── optimization-demo.html  # ⭐ AI 优化模块演示页（排期/竞品/看板）
│   ├── scripts/build_chuangshi_db.py # ⭐ 创视数据清洗+建库+生成售卖模版
│   ├── data/chuangshi_local.db        # ⭐ 创视业务库（3964 点位）
│   ├── data/chuangshi_data.json       # 创视内嵌 HTML 的数据 bundle
│   └── venv/
├── demo.html                    # 前端 Demo（腾讯地图）
├── chuangshi_sales_template.html # ⭐ 创视单文件售卖模版（搜索+CPM+统计）
├── docs/
│   ├── schema.sql             # pDOOH 数据库 Schema
│   ├── bus-pdooh-prd.md       # ⭐ bus-pDOOH 产品需求文档
│   ├── bus-pdooh-system-design.md # ⭐ bus-pDOOH 系统设计
│   ├── pdoh_whitepaper_v2.md  # 项目白皮书（含青柠5V论证）
│   ├── industry_standard_terms_and_guide.md # ⭐ 行业标准术语表+应用指南（T/CCSA 738-2025）
│   ├── prd_qinglin_booking_p0.md      # ⭐ 青柠 Booking P0 需求文档
│   ├── design_qinglin_booking_p0.md   # ⭐ 青柠 Booking P0 设计文档
│   ├── chuangshi_data_architecture.md # ⭐ 创视媒体 CPM + 统计架构文档
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

### chuangshi_local.db（创视广东媒体资源库，3,964 条）

| 表名 | 记录数 | 说明 |
|------|--------|------|
| 大屏点位 | **239** | 写字楼大屏广告位 |
| 电梯LCD屏点位 | **3,725** | 写字楼电梯 LCD 屏广告位 |
| 点位合计 | **3,964** | 单屏设备级，广东省 12 城市 / 513 栋楼 |

---

## 🚧 开发路线图

- [x] **v2.0** pDOOH 数据库设计 + 真实数据 API
- [x] `demo.html` 连接真实数据库
- [x] A2A MCP Server 接口
- [x] 青柠 5V 数据模型论证白皮书
- [x] **⭐ bus-pDOOH 子系统**完整实现（线路管理/竞价引擎/AI审核/效果归因/演示页）
- [x] **⭐ 行业标准对齐**（T/CCSA 738-2025 曝光测量术语表+应用指南）
- [x] **⭐ 青柠智能助手（qinglin_assistant）垂直切片**（知识库真查 + 演示态报备/锁点/导点 + 纯对话 Ollama 关时硬 503 不造假；8/8 回归通过）
- [x] **⭐ 青柠 Booking 真实锁位模块（P0）**（四层超卖防护 + 幂等 + 到期释放 + 9 端点；10/10 并发/ETL 测试通过）
- [x] **⭐ 创视媒体资源子系统**（数据清洗 + SQLite 业务库 3964 点位 + 单文件售卖模版 + CPM 架构；jsdom 真跑 0 崩溃）
- [ ] v2.1 行业标准曝光计算引擎（流动/驻留曝光 + SOT + 曝光乘数 + 接触频次）
- [ ] v2.1 接入真实青柠数据（广州试点）
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

> 服务：**pDOOH A2A MCP Server** · 工具总数：**22 个** · 健康检查：✅ OK · 数据库：`qinlin_local.db`（完整版）· 总数据量：**100,000+ 条**

**✅ 核心投放工具（7个）**

| # | 工具名 | 功能 | 状态 |
|---|--------|------|------|
| 1 | `pdooh_query_screens` | 查询智能屏点位 | ✅ |
| 2 | `pdooh_get_screen_audience` | 获取屏人群画像 | ✅ |
| 3 | `pdooh_create_campaign` | 创建投放计划 | ✅ |
| 4 | `pdooh_query_campaigns` | 查询投放计划 | ✅ |
| 5 | `pdooh_submit_creative` | 提交创意物料 | ✅ |
| 6 | `pdooh_query_report` | 查询效果报告 | ✅ |
| 7 | `pdooh_compliance_check` | 合规审核 | ✅ |

**✅ 点位查询工具（7个）**

| # | 工具名 | 功能 | 数据来源 | 状态 |
|---|--------|------|----------|------|
| 8 | `pdooh_query_access_points` | 门禁点位查询 | 门禁点位（66,308条） | ✅ |
| 9 | `pdooh_query_smart_frames` | 单元门点位查询 | 单元门点位（8,114条） | ✅ |
| 10 | `pdooh_query_daocha_points` | 道闸点位查询 | 道闸点位（1,021条） | ✅ |
| 11 | `pdooh_query_led_points` | 商场LED点位查询 | LED点位（1,365条） | ✅ |
| 12 | `pdooh_query_elevator_frames` | 电梯框架查询 | 预留接口 | ✅ |
| 13 | `pdooh_query_smart_screen` | 智能屏L9查询 | 智能屏L9（9,801台） | ✅ |
| 14 | `pdooh_query_shadow_points` | 投影点位查询 | 预留接口 | ✅ |

**✅ 本地数据库工具（3个）**

| # | 工具名 | 功能 | 状态 |
|---|--------|------|------|
| 15 | `pdooh_query_local_screens` | 本地智能屏查询 | ✅ |
| 16 | `pdooh_query_local_stats` | 本地统计查询 | ✅ |
| 17 | `pdooh_search_local_community` | 本地社区搜索 | ✅ |

**✅ 资源统计工具（3个）**

| # | 工具名 | 功能 | 状态 |
|---|--------|------|------|
| 18 | `pdooh_query_city_resources` | 城市资源统计 | ✅ |
| 19 | `pdooh_query_city_summary` | 全国城市汇总 | ✅ |
| 20 | `pdooh_query_customers` | 客户通讯录查询 | ✅ |

**✅ AI能力工具（2个）**

| # | 工具名 | 功能 | 状态 |
|---|--------|------|------|
| 21 | `pdooh_audience_insight` | 人群洞察分析 | ✅ |
| 22 | `pdooh_calc_roi` | ROI计算 | ✅ |

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

---

## 🤖 AI Agent 服务 (v2.0 新增)

### Tom Agent (5003) - CPM 计算

| 项目 | 值 |
|------|-----|
| 地址 | `http://47.253.159.62:5003` |
| 版本 | v2.0 |
| 功能 | 智能户外广告投放方案生成、CPM跟踪计算、CPM对比计算 |

**API 端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/plan/generate` | POST | 生成投放方案 |
| `/api/cpm/track` | POST | CPM跟踪计算 |
| `/api/cpm/compare` | POST | CPM对比计算 |

**调用示例**：

```bash
# 生成投放方案
curl -X POST http://47.253.159.62:5003/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{"brand":"比亚迪","budget":"30万","city":"广州"}'
```

---

### ROI Agent (5004) - ROI 计算

| 项目 | 值 |
|------|-----|
| 地址 | `http://47.253.159.62:5004` |
| 版本 | v2.0 |
| 功能 | 社区精准营销ROI计算（三场景：悲观/中性/乐观） |

**API 端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/roi` | POST | ROI三场景计算 |
| `/api/compare` | GET | 行业ROI对比 |

**调用示例**：

```bash
# ROI计算
curl -X POST http://47.253.159.62:5004/api/roi \
  -H "Content-Type: application/json" \
  -d '{"frames":5000,"period_weeks":2,"plan_type":"A"}'
```

**ROI 三场景说明**：

| 场景 | 记忆率 | 客单价 | ROI |
|------|--------|--------|-----|
| 悲观 | 15% | 20元 | 21% |
| 中性 | 18% | 22元 | 61% |
| 乐观 | 22% | 25元 | 173% |

---

### 竞品Agent (5005) - 竞品监控

| 项目 | 值 |
|------|-----|
| 地址 | `http://47.253.159.62:5005` |
| 版本 | v2.0 |
| 功能 | 竞品数据库、市场情报、品牌动态 |

**API 端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/competitors` | GET | 竞品列表 |
| `/api/intelligence` | GET | 市场情报 |
| `/api/intelligence/search` | GET | 搜索情报 |

**调用示例**：

```bash
# 竞品列表
curl http://47.253.159.62:5005/api/competitors

# 市场情报搜索
curl 'http://47.253.159.62:5005/api/intelligence/search?q=麦当劳'
```

---

### BabyAGI (5006) - 任务自动化编排引擎 ⭐ 新增

| 项目 | 值 |
|------|-----|
| 地址 | `http://47.253.159.62:5006` |
| 版本 | v1.0 |
| 功能 | 任务队列管理、自动编排、多任务串联执行 |

**核心能力**：

- 🎯 **智能任务解析**：中文描述自动识别城市 + 功能类型
- 🔗 **多任务串联**：自动创建并执行多个关联任务
- 📊 **任务状态追踪**：实时查看所有任务执行状态
- 🎮 **演示模式**：一键运行预设任务组合

**支持的任务类型**：

| 任务关键词 | 功能 | 示例 |
|:-----------|:-----|:-----|
| `查询XX单元门` | 查询单元门点位 | `查询广州单元门点位` |
| `查询XX门禁` | 查询门禁点位 | `查询深圳门禁点位` |
| `查询XX智能屏` | 查询智能屏点位 | `查询成都智能屏点位` |
| `ROI计算` | ROI投资回报计算 | `ROI计算 5000框两周` |
| `生成XX方案` | 生成投放方案 | `生成比亚迪广州50万方案` |

**API 端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/task/add` | POST | 添加任务（中文描述） |
| `/api/task/execute/<task_id>` | POST | 执行任务 |
| `/api/tasks` | GET | 查看所有任务 |
| `/api/demo` | GET | 演示模式（自动跑3个任务） |

**调用示例**：

```bash
# 添加任务
curl -X POST http://47.253.159.62:5006/api/task/add \
  -H "Content-Type: application/json" \
  -d '{"description": "查询广州单元门点位"}'

# 执行任务（假设返回 id=1）
curl -X POST http://47.253.159.62:5006/api/task/execute/1

# 查看所有任务
curl http://47.253.159.62:5006/api/tasks

# 演示模式（自动跑3个任务）
curl http://47.253.159.62:5006/api/demo
```

**Python 调用示例**：

```python
import requests

BASE_URL = "http://47.253.159.62:5006"

# 添加并执行任务
task_id = requests.post(f"{BASE_URL}/api/task/add",
    json={"description": "查询广州单元门点位"}).json()["task"]["id"]

result = requests.post(f"{BASE_URL}/api/task/execute/{task_id}").json()
print(result)
```

> 📖 **完整使用指南**：[`docs/babyagi-5006-guide.md`](docs/babyagi-5006-guide.md)

---

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
![控制面板]<img width="2450" height="1113" alt="ScreenShot_2026-06-19_225619_151" src="https://github.com/user-attachments/assets/2e33a300-9cdd-4731-be22-81f88fdf54b4" />
<img width="2549" height="1352" alt="image" src="https://github.com/user-attachments/assets/2ba4d673-5e96-4fd0-9dc7-518952d3ba87" />




*实时数据概览：点位统计、曝光量、点击率、活跃计划*

### 🔍 点位查询（Point Search）
[点位查询]<img width="2493" height="1245" alt="ScreenShot_2026-06-19_224855_063" src="https://github.com/user-attachments/assets/64b656c0-cd7d-4499-bf39-5b372b6fde48" />


*智能筛选：城市/区域/媒体类型/价格区间*

### 📅 投放计划（Ad Plans）
[投放计划]<img width="2064" height="684" alt="ScreenShot_2026-06-19_225516_249" src="https://github.com/user-attachments/assets/4758432f-ab62-4c16-80a7-09639dcfa31c" />


*计划管理：创建/编辑/暂停/结束，AI 优化建议*

### 📊 ROI 计算器（ROI Calculator）
[ROI 计算器]<img width="2481" height="1215" alt="ScreenShot_2026-06-19_224924_084" src="https://github.com/user-attachments/assets/c9e825b1-3c2a-478f-b191-0e2db126f99b" />
<img width="2478" height="1323" alt="image" src="https://github.com/user-attachments/assets/dbb9072e-93d6-455e-a267-b263c5021f15" />


*智能预算分配：UV/PV/转化率/LTV/ROI 一键计算*

### 🏆 竞品分析（Competitor Analysis）
[竞品分析]<img width="1779" height="1026" alt="ScreenShot_2026-06-19_224941_885" src="https://github.com/user-attachments/assets/f4738cd8-ed21-44c6-9a0e-a2e4ef322a81" />


*市场洞察：份额对比/策略分析/趋势预测*

### ⚙️ 系统设置（Settings）
[系统设置]!<img width="1725" height="1131" alt="ScreenShot_2026-06-19_225011_780" src="https://github.com/user-attachments/assets/e4aa3f52-45a2-4130-aa43-fb3a5e23a782" />



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
