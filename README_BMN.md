# BMN 品牌智能增长操作系统

> **Brand Marketing Next** — 基于 LangGraph + ChromaDB + FastAPI 的智能化品牌营销系统

![BMN L1-L5 架构](docs/bmn_architecture.svg)

---

## 系统概述

BMN（Brand Marketing Next）是一个五层架构的智能化品牌营销操作系统，旨在帮助品牌方实现：

1. **品牌引擎（L1）**：统一管理品牌身份、价值主张、信任背书
2. **资产金库（L2）**：结构化存储八大类营销资产，支持语义检索
3. **智能工作流（L3）**：基于 LangGraph 的自动化营销内容生成
4. **Prompt 路由器（L4）**：智能分发任务到最适合的 LLM/Prompt 模板
5. **前端界面（L5）**：可视化操作界面，降低使用门槛

### 核心能力

- ✅ **品牌配置管理**：一键获取完整品牌配置（身份/价值/差异化/信任背书）
- ✅ **资产语义检索**：基于 ChromaDB 的向量搜索，快速找到相关营销资产
- ✅ **智能文案生成**：输入原始素材，自动生成小红书/朋友圈/PPT 大纲
- ✅ **合规检查**：自动检查生成内容的合规性（风险等级标注）
- ✅ **资产自动归档**：工作流生成的文案自动保存到资产金库

---

## 核心架构

### 五层架构总览

![BMN L1-L5 架构](docs/bmn_architecture.svg)

**数据流**：L1（品牌引擎）→ L2（资产金库）→ L3（工作流工厂）→ L4（多维分发）→ L5（指标仪表盘）→ 闭环反馈至 L1

---

### L1 品牌逻辑引擎 · Brand Strategy Engine

| 组件 | 说明 |
|------|------|
| 身份定位 | 品牌是谁？核心价值主张是什么？ |
| 价值定位 | 为用户解决什么问题？差异化是什么？ |
| 信任背书 | 权威认证、客户案例、数据证明 |
| Master Prompt | 自动生成注入到所有 LLM 调用的系统提示词 |

**输出**：`master_prompt`（注入到 L3 所有工作流）

---

### L2 数字资产金库 · Digital Asset Vault

| 资产类型 | 说明 |
|----------|------|
| 品牌诉求 | 品牌方原始需求文档 |
| 产品卖点 | 产品核心优势、差异化特征 |
| 用户场景 | 使用场景、痛点、动机 |
| 客户案例 | 历史成功案例（结构化） |
| 行业知识 | 行业趋势、竞品分析 |
| 视觉规范 | 配色、字体、版式要求 |
| 问答口径 | 标准话术、禁忌用语 |
| 风险边界 | 合规红线、广告法禁忌 |

**技术实现**：PostgreSQL（结构化存储）+ ChromaDB（向量检索）

---

### L3 AI工作流工厂 · AI Production Factory

九大标准化工作流：

| 工作流 | 说明 | 状态 |
|----------|------|------|
| 新品上市 | 完整上市方案生成 | ✅ 已完成 |
| 案例生成 | 客户案例结构化重写 | ✅ 已完成 |
| 多渠道改写 | 同一内容适配小红书/朋友圈/公众号 | ⏳ 开发中 |
| 风险校验 | 合规检查、广告法校验 | ✅ 已完成 |
| 竞品分析 | 自动抓取竞品数据并生成报告 | 📋 计划中 |
| 效果归因 | 分析广告效果并优化策略 | 📋 计划中 |
| 选题策划 | 「选题虾」：生成广告选题 | ✅ 已完成 |
| 文案创作 | 「文案虾」：生成多版本文案 | ✅ 已完成 |
| 审核发布 | 「审核虾」：合规审核 + 质量评分 | ✅ 已完成 |

**技术实现**：LangGraph + FastAPI，状态机编排

---

### L4 多维分发适配器 · Intelligent Distribution Hub

| 受众 | 语言 | 示例 |
|------|------|------|
| 用户 | 体验语言 | "更便捷""更安心""更有趣" |
| 客户 | 价值语言 | "ROI提升 30%""品牌认知度+25%" |
| 渠道 | 生意语言 | "分成比例 18%""CPS 2.0 动态分成" |
| 投资人 | 增长语言 | "月活 600 万+""覆盖 70,000+ 小区" |

**技术实现**：规则引擎 + LLM 模板匹配

---

### L5 增长指标仪表盘 · Management Feedback Dashboard

| 指标维度 | 具体指标 | 数据来源 |
|------------|----------|----------|
| 认知指标 | 品牌提及率、搜索指数、媒体曝光量 | 友盟 + 百度指数 |
| 信任指标 | 案例下载量、官网访问深度、留资率 | 官网 + CRM |
| 互动指标 | 内容点赞/评论/转发、社群活跃度 | 社交媒体 API |
| 转化指标 | 留资成本 CPL、转化成本 CAC、ROI | 广告投放系统 |
| 资产指标 | 内容产出量、资产复用率、工作流执行次数 | BMN 内部统计 |

**技术实现**：Chart.js + FastAPI + PostgreSQL

---

### 闭环反馈 / 自进化

```
Step 1：资产数字化（L1 + L2 底层构建）
   ↓
Step 2：工作流自动化（L3 场景驱动）
   ↓
Step 3：系统自进化（L4 + L5 闭环优化）
   ↓
L5 指标仪表盘反馈 → 调整 L1 Master Prompt → 优化 L3 工作流
```

---

---

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **L1 品牌引擎** | JSON + Prompt 模板 | 轻量级，易于扩展 |
| **L2 资产金库** | PostgreSQL + ChromaDB | 结构化 + 向量检索 |
| **L3 工作流** | LangGraph + FastAPI | 可视化管线编排 |
| **L4 Prompt 路由** | 规则引擎 + LLM 元数据 | 智能分发 |
| **L5 前端** | Vue 3 + Element Plus | 现代化 UI |

### 依赖环境

- **Python 3.13+**
- **FastAPI**：Web 框架
- **LangChain/LangGraph**：工作流编排
- **ChromaDB**：向量数据库
- **sentence-transformers**：文本向量化
- **PostgreSQL**：关系型数据库（复用 AIAdPlacer 的数据库）
- **Vue 3**（可选）：前端框架

---

## 快速开始

### 1. 启动后端服务

```bash
# 进入项目目录
cd D:/Mirofish/AIAdPlacer/backend

# 激活虚拟环境
source venv/Scripts/activate

# 启动 BMN 后端（端口 5003）
USERNAME=user USER=user python -m uvicorn app.bmn_app:app --host 127.0.0.1 --port 5003
```

**验证启动成功**：
```bash
curl http://127.0.0.1:5003/
# 返回：{"msg":"BMN 品牌智能增长操作系统运行中","docs":"/docs"}
```

**API 文档**：http://127.0.0.1:5003/docs

---

### 2. 启动前端 Demo

```bash
# 进入前端目录
cd D:/Mirofish/AIAdPlacer/bmn-frontend

# 启动静态服务器（端口 8080）
python -m http.server 8080
```

**访问前端**：http://127.0.0.1:8080/demo.html

---

### 3. 测试 API

#### 获取品牌配置
```bash
# 使用 Python（避免 curl 中文编码问题）
python -c "
import requests
url = 'http://127.0.0.1:5003/api/v2/bmn/brand/config?brand_name=亲邻传媒'
resp = requests.get(url)
print(resp.json())
"
```

#### 搜索资产（语义检索）
```python
import requests

url = 'http://127.0.0.1:5003/api/v2/bmn/assets/search'
data = {'query': '社区营销', 'asset_type': '', 'top_k': 3}
resp = requests.post(url, json=data)
print(resp.json())
```

#### 执行工作流（生成文案）
```python
import requests

url = 'http://127.0.0.1:5003/api/v2/bmn/workflows/case_study/run'
data = {
    'raw_material': '亲邻传媒社区媒体资源，覆盖70000+小区，开门App 600万+DAU',
    'client_name': '某日化品牌',
    'industry': '日化',
    'product_info': '新品洗发水社区推广'
}
resp = requests.post(url, json=data)
print(resp.json())
```

---

## API 文档

### L1 品牌引擎 API

#### `GET /api/v2/bmn/brand/config`
获取品牌完整配置。

**参数**：
- `brand_name`（必填）：品牌名称

**返回**：
```json
{
  "id": "xxx",
  "brand_name": "亲邻传媒",
  "identity": "品牌身份描述",
  "value_proposition": "核心价值主张",
  "trust_proof": ["信任背书1", "信任背书2"],
  "differentiation": "差异化定位",
  "master_prompt": "注入到 LLM 的 Master Prompt"
}
```

#### `GET /api/v2/bmn/brand/master_prompt`
获取品牌的 Master Prompt（用于 LLM 调用）。

**参数**：
- `brand_name`（必填）：品牌名称

---

### L2 资产金库 API

#### `GET /api/v2/bmn/assets`
列出所有资产（支持分页）。

**参数**：
- `asset_type`（可选）：资产类型筛选
- `keyword`（可选）：关键词搜索
- `page`（默认 1）：页码
- `page_size`（默认 20）：每页数量

#### `POST /api/v2/bmn/assets/search`
语义检索资产（ChromaDB 向量搜索）。

**请求体**：
```json
{
  "query": "社区营销",
  "asset_type": "",
  "top_k": 5
}
```

**返回**：
```json
{
  "results": [
    {
      "content": "资产内容（前 300 字）",
      "metadata": {"title": "标题", "asset_type": "类型"},
      "relevance_score": 0.6895,
      "asset": {"id": "xxx", "title": "标题", ...}
    }
  ],
  "total": 1
}
```

#### `POST /api/v2/bmn/assets`
新增资产。

#### `GET /api/v2/bmn/assets/{asset_id}`
查询单条资产详情。

#### `DELETE /api/v2/bmn/assets/{asset_id}`
删除资产。

---

### L3 工作流 API

#### `POST /api/v2/bmn/workflows/case_study/run`
执行客户案例生成工作流。

**请求体**：
```json
{
  "raw_material": "原始素材（必填）",
  "client_name": "客户名称（必填）",
  "industry": "行业（可选）",
  "product_info": "产品信息（可选）"
}
```

**返回**：
```json
{
  "ok": true,
  "workflow_run_id": "运行记录 ID",
  "result": {
    "copies": {
      "xhs": "小红书文案",
      "moments": "朋友圈文案",
      "ppt_outline": "PPT 大纲"
    }
  },
  "compliance": ["⚠️ 中风险：到达率数据未注明来源"],
  "asset_saved": true,
  "asset_id": "保存到资产库的 ID"
}
```

#### `GET /api/v2/bmn/workflows/runs`
查询工作流运行记录。

#### `GET /api/v2/bmn/workflows/runs/{run_id}`
查询单条运行记录详情。

---

## 工作流说明

### 案例生成工作流（case_study）

```
输入：原始素材 + 客户名称 + 行业 + 产品信息
        ↓
Step 1：加载品牌配置（L1）
        ↓
Step 2：检索相关资产（L2）
        ↓
Step 3：生成文案（调用 LLM）
  ├─ 小红书文案
  ├─ 朋友圈文案
  └─ PPT 大纲
        ↓
Step 4：合规检查（风险等级标注）
        ↓
Step 5：保存结果到资产库（L2）
        ↓
输出：copies + compliance + asset_id
```

### 扩展工作流（开发中）

- **文案创作工作流**：批量生成多平台文案
- **竞品分析工作流**：自动抓取竞品数据并生成报告
- **效果归因工作流**：分析广告效果并优化策略

---

## 前端界面

### 页面结构

1. **品牌引擎（L1）**
   - 输入品牌名称
   - 展示完整品牌配置
   - 复制 Master Prompt

2. **资产金库（L2）**
   - 资产列表（支持类型筛选/关键词搜索）
   - 资产详情查看
   - 语义搜索结果展示

3. **工作流（L3）**
   - 表单输入（原始素材/客户名称/行业/产品信息）
   - 执行工作流
   - 展示生成结果（文案 + 合规检查）

### UI 特性

- ✅ 现代化设计（渐变/阴影/圆角）
- ✅ 加载动画（spinner）
- ✅ 响应式布局（移动端适配）
- ✅ 更好的信息层次结构

---

## 开发路线图

### ✅ 已完成（Phase 1-2）

- [x] L1 品牌引擎（数据模型 + API）
- [x] L2 资产金库（数据模型 + ChromaDB 集成 + API）
- [x] L3 工作流（案例生成管线 + API）
- [x] 前端 Demo（静态 HTML + Vanilla JS）
- [x] Windows 兼容性修复（mock pwd 模块 + 环境变量）
- [x] ChromaDB 初始化修复
- [x] UI 优化

### ⏳ 进行中（Phase 3）

- [ ] L4 Prompt 路由器
- [ ] 更多工作流（文案创作/竞品分析/效果归因）
- [ ] 前端 Vue 项目（替代静态 HTML）

### 📋 计划中（Phase 4-5）

- [ ] L5 数据看板（Chart.js 可视化）
- [ ] 用户系统（多品牌支持）
- [ ] API 鉴权（JWT Token）
- [ ] 部署脚本（Docker + Nginx）
- [ ] 单元测试覆盖率 >80%

---

## 文件结构

```
D:/Mirofish/AIAdPlacer/backend/
├── app/
│   ├── bmn_app.py              # BMN 独立启动文件
│   ├── bmn/
│   │   ├── __init__.py
│   │   ├── models.py           # L1-L2 数据模型
│   │   ├── brand_engine.py     # L1 品牌引擎逻辑
│   │   ├── asset_vault.py     # L2 资产金库逻辑
│   │   ├── seed_qinlin_data.py # 初始数据种子
│   │   ├── api/
│   │   │   ├── brand_routes.py
│   │   │   ├── asset_routes.py
│   │   │   └── workflow_routes.py
│   │   └── workflows/
│   │       └── case_study.py  # L3 工作流实现
│   └── models.py              # 共享数据模型（SessionLocal）
├── bmn-frontend/
│   └── demo.html              # 前端 Demo
└── README_BMN.md              # 本文档
```

---

## 常见问题（FAQ）

### Q1：ChromaDB 初始化失败怎么办？

**A**：确保设置了环境变量 `USERNAME` 和 `USER`。

```bash
USERNAME=user USER=user python -m uvicorn app.bmn_app:app ...
```

### Q2：为什么 curl 请求返回 "There was an error parsing the body"？

**A**：curl 对中文请求体的编码支持不好。请使用 Python requests 库发送请求。

### Q3：如何查看 API 文档？

**A**：启动后端后访问 http://127.0.0.1:5003/docs

### Q4：工作流执行失败怎么办？

**A**：检查是否配置了 LLM（Ollama 或其他）。当前工作流依赖 LLM 生成文案。

---

## 漏洞与已知问题

> ⚠️ **重要说明**：本项目为实验性研究项目，部分功能尚不稳定，请谨慎用于生产环境。

### 已确认问题

| 问题 | 影响 | 状态 | 解决方案 |
|------|------|------|----------|
| LLM JSON 输出不稳定 | 三只虾系统解析失败 | ⚠️ 已知 | 使用 `json5` 宽容解析器；Prompt 强制要求不换行 |
| BMN 后端启动失败 | 无法运行 `bm_app.py` | ⚠️ 已知 | ChromaDB 依赖 `pwd` 模块，Windows 需 mock；已修复 |
| Ollama 推理速度慢 | 9B 模型响应 60-120 秒 | ⚠️ 已知 | 换用 3B 轻量模型；或设置 `DEMO_MODEL` 环境变量 |
| `.env` 字段未同步 | Pydantic Settings 报 `Extra inputs not permitted` | ✅ 已修复 | `config.py` 已添加 `LLM_PROVIDER` 等字段 |
| 三只虾 Demo 超时 | 120 秒默认超时不够 | ⚠️ 已知 | 已更新为 180 秒；建议使用更轻量模型 |
| PostgreSQL 连接失败 | 后端无法启动 | ⚠️ 需配置 | 确保 PostgreSQL 服务运行在 `127.0.0.1:5432`，数据库 `ai_adplacer` 已创建 |
| Redis 连接失败 | 缓存功能不可用 | ⚠️ 需配置 | Windows 需安装 Redis 3.0.504；或注释掉 Redis 相关代码 |
| 前端 Vue 项目未完成 | L5 仪表盘无界面 | 📋 计划中 | 当前可用静态 HTML Demo（`bm-frontend/demo.html`） |

### 安全风险

| 风险 | 说明 | 缓解措施 |
|------|------|----------|
| `.env` 文件泄露 | 包含数据库密码、API Key | 已加入 `.gitignore`，**切勿提交到 GitHub** |
| LLM 生成内容未经审核 | 可能输出违规内容 | 「审核虾」模块进行合规检查；人工二次审核 |
| SQL 注入 | 用户输入未充分校验 | 使用 SQLAlchemy ORM；LLM 输入需做长度限制 |
| 跨端归因数据隐私 | Cookie-ID 匹配涉及用户隐私 | 数据脱敏处理；仅存储匹配率统计 |

### 降级方案

当 LLM 不可用时的降级策略：

| 模块 | 降级方案 |
|------|----------|
| 选题虾 | 返回预设行业选题模板 |
| 文案虾 | 使用规则模板 + 变量替换 |
| 审核虾 | 基础关键词过滤（违禁词库） |
| 品牌引擎 | 返回静态配置文件 |
| 资产检索 | 仅支持关键词搜索，禁用向量检索 |

### 已知限制

1. **模型依赖**：当前默认使用 `modelscope.cn/diodel/Qwen3.5-9B-Q4_K_M-GGUF:latest`，需自行下载（约 5.6GB）
2. **Windows 兼容性**：ChromaDB 在 Windows 需要 mock `pwd` 模块（已处理）
3. **并发性能**：Ollama 单进程，不支持高并发；建议生产环境使用 API 调用
4. **前端依赖**：L5 仪表盘需要 Chart.js，当前仅提供静态 HTML Demo

---

## 联系与贡献

- **作者**：Tom（亲邻传媒华南区 AI 负责人）
- **项目**：BMN 品牌智能增长操作系统
- **仓库**：`D:/Mirofish/AIAdPlacer/`

---

## 许可证

MIT License

---

**最后更新**：2026-05-08
