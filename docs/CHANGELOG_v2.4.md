# AIAdPlacer 版本更新说明 v2.4.0

**发布日期**：2026-06-17  
**版本代号**：Tom × ROI 联动版

---

## 概述

v2.4.0 实现了 **Tom Agent（户外广告投放专家）** 与 **ROI Agent（广告投放 ROI 计算专家）** 的自动联动。  
当用户通过 Tom Agent 生成投放方案时，系统会自动调用 ROI Agent 计算三场景 ROI（悲观/中性/乐观），并将结果随方案一并返回。

---

## 新增功能

### 1. Tom Agent ↔ ROI Agent 联动

**触发条件**：调用 `POST /api/v2/tom/plan/generate` 生成投放方案

**联动流程**：
```
用户输入（品牌/产品/预算/城市）
        ↓
Tom Agent 生成媒体组合方案
        ↓
自动调用 ROI Agent（/api/v2/roi/three-scenarios）
        ↓
返回完整响应（含 ROI 三场景结果）
```

**联动实现**：
- 在 `tom_agent.py` 新增 `call_roi_agent(cost, cities)` 异步函数
- 使用 `httpx.AsyncClient` 调用 ROI Agent HTTP 接口
- ROI Agent 端口：5004
- 调用失败时不阻断主流程（降级处理，返回 `roi_result: null`）

**响应示例**：
```json
{
  "plan_id": "PLAN-A1B2C3D4",
  "brand": "黑人牙膏",
  "total_cost": 100000,
  "roi_result": {
    "pessimistic": {"roi_percent": 131.5, "ltv": 231500, ...},
    "neutral":      {"roi_percent": 181.6, "ltv": 281600, ...},
    "optimistic":   {"roi_percent": 252.3, "ltv": 352900, ...}
  }
}
```

---

### 2. 一键启动所有 Agent（`run_all_agents.py`）

**功能**：一键启动 AIAdPlacer 所有 Agent 服务（含健康检查等待）

**启动方式**：
```bash
cd D:/Mirofish/AIAdPlacer/backend
python run_all_agents.py
```

**启动的服务**（端口分配）：
| Agent | 端口 | 功能 |
|--------|------|------|
| MCP Server | 5002 | pDOOH MCP 工具（22个） |
| Tom Agent | 5003 | 户外广告投放专家 |
| ROI Agent | 5004 | 广告投放 ROI 计算专家 |
| 竞品监测 Agent | 5005 | 竞品数据查询与对比 |

**健康检查**：
- 启动后自动等待所有 Agent 健康检查通过（超时 30 秒）
- 健康检查地址：<`http://127.0.0.1:{port}/health`>

---

## 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/tom_agent.py` | 修改 | 新增 `import httpx`；新增 `call_roi_agent()` 函数；`PlanGenerateResponse` 增加 `roi_result` 字段；`/plan/generate` 端点自动调用 ROI Agent；System Prompt 更新 |
| `backend/run_all_agents.py` | **新增** | 一键启动所有 Agent（含健康检查） |
| `docs/CHANGELOG_v2.4.md` | **新增** | 本版本更新说明 |

---

## 技术细节

### Tom Agent 调用 ROI Agent 的实现

**函数签名**：
```python
async def call_roi_agent(cost: float, cities: List[str]) -> Optional[Dict]:
    """
    调用 ROI Agent 计算三场景 ROI
    返回格式：{
        "pessimistic": {"roi_percent": ..., ...},
        "neutral":      {...},
        "optimistic":   {...}
    }
    """
```

**调用 URL**：
```
GET http://127.0.0.1:5004/api/v2/roi/three-scenarios?N={N}&cost={cost}&T=14
```
其中 `N = min(len(cities), 3) * 5000`（每城市 5000 框，最多 3 个城市）

**异常处理**：
- ROI Agent 未启动（Connection Refused）→ 返回 `None`，不影响方案生成
- ROI Agent 返回非 200 → 记录 warning 日志，返回 `None`
- httpx 超时（10 秒）→ 记录 warning 日志，返回 `None`

---

### ROI Agent 三场景计算公式（联动返回的数据）

来源于 `duckwolf.cn/10.html`（黑人牙膏 × 皓邻传媒合作方案 v5.0）

| 场景 | 记忆率 r | 客单价 a | 复购系数 f | ROI 示例（成本 10 万） |
|------|----------|----------|------------|---------------------|
| 悲观 | 15% | 20 元 | 1.3 | 131.5% |
| 中性 | 18% | 22 元 | 1.4 | 181.6% |
| 乐观 | 22% | 25 元 | 1.5 | 252.3% |

**核心公式**：
```
UV   = N × U × P × β
PV   = UV × γ × T
记忆 = UV × r
转化 = 记忆 × c
首销 = 转化 × a
LTV  = 首销 × (1 + f)
ROI  = (LTV - 成本) / 成本 × 100%
```

---

## 测试方法

### 1. 启动所有 Agent
```bash
cd D:/Mirofish/AIAdPlacer/backend
python run_all_agents.py
```

### 2. 测试联动功能
```bash
curl -X POST http://127.0.0.1:5003/api/v2/tom/plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "黑人牙膏",
    "product": "双重薄荷牙膏 120g",
    "budget": 100000,
    "cities": ["广州"],
    "target_audience": "社区居民（家庭决策者）",
    "goals": ["提升品牌知名度", "促进销售转化"]
  }'
```

**预期结果**：
- 返回 HTTP 200
- 响应体包含 `roi_result` 字段
- `roi_result` 包含 `pessimistic` / `neutral` / `optimistic` 三个场景

### 3. 单独测试 ROI Agent
```bash
curl "http://127.0.0.1:5004/api/v2/roi/three-scenarios?N=5000&cost=100000&T=14"
```

---

## 升级建议

### 已有部署升级步骤
1. 拉取最新代码：`git pull origin master`
2. 安装新增依赖：`pip install httpx`
3. 启动所有 Agent：`python run_all_agents.py`
4. 测试联动功能（见「测试方法」）

### 新部署步骤
1. 克隆仓库：`git clone https://github.com/tomwugdgz/AIAdPlacer.git`
2. 安装依赖：`pip install -r requirements.txt`（含 `httpx`）
3. 配置环境变量（`.env`）：`OPENAI_API_KEY`, `DATABASE_URL`, ...
4. 启动所有 Agent：`python run_all_agents.py`

---

## 已知问题

1. **ROI Agent 未启动时联动降级**  
   - 现象：Tom Agent 生成方案成功，但 `roi_result` 为 `null`  
   - 原因：ROI Agent（端口 5004）未启动  
   - 解决：先启动 ROI Agent，或忽略（降级处理）

2. **`call_roi_agent` 使用固定参数**  
   - 现象：ROI 计算使用默认参数（U=100, P=2.51, β=0.85, ...）  
   - 改进方向：根据城市、产品自动调整参数（下版本实现）

---

## 下一步计划（v2.5.0）

1. **参数自动调整**  
   - 根据城市自动调整 `U`（每栋楼户数）  
   - 根据产品自动调整 `a`（客单价）和 `r`（记忆率）

2. **联动结果可视化**  
   - 在 Tom Agent 的响应里加入 ROI 可视化图表（HTML）  
   - 支持导出 PDF 投放方案报告

3. **多 Agent 编排器**  
   - 创建 `orchestrator.py`，支持复杂工作流（Tom → ROI → 竞品监测 → 输出报告）  
   - 使用 LangGraph 实现 Agent 编排

---

## 贡献者

- **Tom**（户外广告投放专家）：需求设计、媒体组合策略
- **ROI Agent**（ROI 计算引擎）：公式实现、三场景计算
- **Qi**（交付总监）：联动架构设计、代码实现

---

## 相关文档

- [产品规格说明书 v2](./AIAdPlacer-Product-Specification-v2.md)
- [用户使用说明书](./AIAdPlacer-User-Manual.md)
- [MCP 工具调用手册](./MCP-Tool-Calling-Guide.md)
- [ROI Agent 调用指南](./ROI-Agent-User-Guide.md)

---

**端点到端到，Tom 帮你算 ROI！** 🤝📊
