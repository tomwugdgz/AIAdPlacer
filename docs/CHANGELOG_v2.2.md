# AIAdPlacer 版本更新说明 v2.2.0

**发布日期**: 2026-06-17  
**版本代号**: Tom Agent 接入版

---

## 🎯 本次更新概览

新增 **Tom Agent（户外广告投放专家）** 完整模块，支持自然语言对话、投放方案生成、CPM 追踪对比、点位查询等功能，并接入现有 MCP 工具（22个）。

---

## 🆕 新增功能

### 1. Tom Agent 服务 (`backend/app/tom_agent.py`)

**端口**: 5003（独立服务）/ 内嵌路由 `/api/v2/tom/*`

**核心能力**:
- 🤖 **LLM 驱动对话**：基于 OpenAI 兼容接口，支持流式/非流式响应
- 📋 **投放方案生成**（`/plan/generate`）：根据品牌、预算、城市自动生成媒体组合方案
- 📊 **CPM 追踪**（`/cpm/track`）：查询投放计划的曝光、点击、CTR、CPM 数据
- 📈 **CPM 对比**（`/cpm/compare`）：对比多个投放计划的效果指标
- 🗺️ **自然语言点位查询**（`/query/points`）：将自然语言转换为 MCP 工具调用
- 🔌 **MCP 工具自动调用**：根据用户消息智能检测并调用 22 个 MCP 工具

**Tom Agent 人设** (System Prompt):
- 专业的户外广告投放专家，深入的市场洞察
- 主推媒体：单元门灯箱（30%~48%）> 广告门 > 开门App
- 熟悉亲邻传媒资源（70,000+ 小区，3 亿城镇家庭）
- 联系方式统一：17665188615
- 竞品话术：将"华语传媒"改为"亲邻传媒"

**API 端点**:

| 端点 | 方法 | 功能 |
|--------|------|------|
| `/api/v2/tom/health` | GET | 健康检查 |
| `/api/v2/tom/chat` | POST | 非流式对话 |
| `/api/v2/tom/chat/stream` | POST | 流式对话（SSE） |
| `/api/v2/tom/plan/generate` | POST | 生成投放方案 |
| `/api/v2/tom/cpm/track` | POST | CPM 数据追踪 |
| `/api/v2/tom/cpm/compare` | POST | CPM 多计划对比 |
| `/api/v2/tom/query/points` | POST | 自然语言点位查询 |
| `/api/v2/tom/tools` | GET | 列出可用 MCP 工具 |

### 2. MCP 工具扩充（v2.1 已完成，v2.2 确认）

**工具数量**: 8 → 22 个

**新增工具列表**:

| # | 工具名称 | 功能 | 数据库 |
|---|----------|------|--------|
| 1 | `pdooh_query_access_points` | 查询门禁点位 | 亲邻门禁全国点位.db |
| 2 | `pdooh_query_screens` | 查询智能屏 | 智能屏2025数据.db |
| 3 | `pdooh_query_gates` | 查询道闸 | 亲邻广州道闸.db |
| 4 | `pdooh_query_led` | 查询商场LED | 亲邻商场LED.db |
| 5 | `pdooh_query_unit_doors` | 查询单元门 | 亲邻单元门智能框架.db |
| 6 | `pdooh_city_report` | 城市资源统计 | 多库联合 |
| 7 | `pdooh_create_plan` | 创建投放计划 | - |
| 8 | `pdooh_update_plan` | 更新投放计划 | - |
| 9 | `pdooh_get_plan` | 获取投放计划 | - |
| 10 | `roi_calculate` | ROI 三场景计算 | - |
| 11 | `customer_query` | 查询客户通讯录 | 客户通讯录.db |
| 12 | `inventory_stats` | 资源库存统计 | - |
| 13 | `pricing_query` | 媒体价格查询 | - |
| 14 | `competitor_query` | 竞品数据查询 | - |
| 15 | `audience_insight` | 人群洞察 | - |
| 16 | `creative_generate` | 创意内容生成 | - |
| 17 | `attribution_report` | 效果归因报告 | - |
| 18 | `knowledge_search` | 知识库检索 | ChromaDB |
| 19 | `knowledge_add` | 知识库添加 | ChromaDB |
| 20 | `elevator_frame_query` | 电梯框架查询 | 电梯框架.db |
| 21 | `projector_screen_query` | 投影屏查询 | 投影屏.db |
| 22 | `bmr_rank_query` | BMR 商圈排名 | - |

### 3. 路由注册更新 (`backend/app/main.py`)

- 新增 `tom_agent_router` 导入和注册
- 启动日志新增 Tom Agent 端点提示
- 版本号保持 `2.0.0`（实际功能已达 v2.2.0）

---

## 🔧 改进优化

1. **System Prompt 专业化**：
   - 完整的 Tom Agent 人设定义（5000+ 字）
   - 包含媒体详情、工作流程、沟通规范
   - 引用 4A 广告公司经典案例能力

2. **MCP 工具智能路由**：
   - 根据用户消息自动检测意图（点位查询/城市统计/报价查询）
   - 自动调用对应 MCP 工具并回传 LLM
   - 支持手动指定 `use_mcp=true/false`

3. **投放方案生成逻辑**：
   - 按预算自动分配媒体组合（单元门 40% / 广告门 30% / App 20% / 其他 10%）
   - 生成时间线（需求确认 → 方案细化 → 合同签署 → 素材准备 → 上线投放）
   - 返回 `plan_id` 便于后续追踪

4. **CPM 追踪与对比**：
   - 支持单计划追踪（`/cpm/track`）
   - 支持多计划对比（`/cpm/compare`）
   - 返回 CTR、CPM、ROI 等指标

---

## 🐛 修复问题

1. **MCP 工具定义不完整**：v2.1 已定义 22 个工具，但部分工具处理逻辑未实现 → v2.2 补充完整处理逻辑（已在 `pdooh_mcp.py` 中）
2. **Tom Agent 未注册**：v2.1 创建了 `competitor_agent.py` 但未注册路由 → v2.2 创建 `tom_agent.py` 并注册到 `main.py`
3. **System Prompt 缺失**：Tom Agent 无专业人设 → v2.2 新增 5000+ 字 System Prompt

---

## 📦 部署说明

### 环境要求
- Python 3.8+
- FastAPI + Uvicorn
- OpenAI API Key（或兼容接口）

### 启动方式

**方式一：独立服务（端口 5003）**
```bash
cd D:/Mirofish/AIAdPlacer/backend
python -m uvicorn app.tom_agent:app --host 0.0.0.0 --port 5003 --reload
```

**方式二：内嵌到主服务（端口 5002）**
```bash
cd D:/Mirofish/AIAdPlacer/backend
python run.py   # 已包含 Tom Agent 路由
```

### 健康检查
```bash
curl http://127.0.0.1:5003/health
# 或（内嵌模式）
curl http://127.0.0.1:5002/api/v2/tom/health
```

### 测试对话
```bash
curl -X POST http://127.0.0.1:5002/api/v2/tom/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "我想在广州投放广告，预算 50 万，推广新上市的洗发水，应该选什么媒体？"}
    ],
    "stream": false,
    "use_mcp": true
  }'
```

---

## 📋 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/tom_agent.py` | **新增** | Tom Agent 完整实现（500 行） |
| `backend/app/main.py` | 更新 | 注册 Tom Agent 路由 + 启动日志 |
| `backend/app/pdooh_mcp.py` | 更新（v2.1） | 22 个 MCP 工具完整实现 |
| `docs/CHANGELOG_v2.2.md` | **新增** | 本版本更新说明 |

---

## 🚀 下一步计划（v2.3）

1. **Tom Agent 独立服务脚本**：创建 `run_tom_agent.py`（端口 5003 独立运行）
2. **LLM Function Calling 完善**：用 `openai.function_call` 替代关键词路由
3. **数据库接入验证**：测试 22 个 MCP 工具的真实数据返回
4. **前端接入**：在 AIAdPlacer 前端添加 Tom Agent 对话界面
5. **多轮对话支持**：维护 `session_id`，支持上下文连续对话

---

## 📊 测试建议

### 功能测试清单
- [ ] 健康检查端点响应正常
- [ ] 非流式对话返回完整内容
- [ ] 流式对话 SSE 格式正确
- [ ] 投放方案生成返回合规 JSON
- [ ] CPM 追踪返回模拟数据
- [ ] CPM 对比正确计算平均值
- [ ] 自然语言点位查询调用正确 MCP 工具
- [ ] MCP 工具自动检测（关键词触发）准确

### 性能测试建议
- 并发对话请求：≥ 10 并发
- 响应时间：P95 < 3s（非流式）/ P95 < 500ms（流式首 token）
- MCP 工具调用超时：≤ 5s

---

## 📞 联系方式

**Tom Agent 统一联系方式**: 17665188615

**技术支援**: 通过 AIAdPlacer GitHub Issues 提交问题

---

*AIAdPlacer v2.2.0 — Tom Agent 接入版*  
*让 AI 成为您的户外广告投放专家*
