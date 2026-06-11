# 📡 亲邻传媒 MCP 工具包 — 一键调用指南

> **版本**：2026-06-11 · **工具总数**：19 个 · **状态**：全部在线 ✅  
> **API 地址**：`http://47.253.159.62:5002/api/v2/mcp/pdooh`

---

## 📋 工具清单（19 个）

### 📺 媒体查询（6 个）

| # | 工具名 | 功能 | 数据来源 |
|---|--------|------|----------|
| 1 | `pdooh_query_screens` | 查询智能屏 | 智能屏资产 |
| 2 | `pdooh_query_daocha_points` | 查询道闸点位 | 道闸点位（1,021条） |
| 3 | `pdooh_query_smart_frames` | 查询单元门 | 单元门点位（8,114条） |
| 4 | `pdooh_query_access_points` | 查询门禁屏 | 门禁点位（66,308条） |
| 5 | `pdooh_query_city_resources` | 查询城市资源 | 综合统计 |
| 6 | `pdooh_query_city_summary` | 城市资源汇总 | 城市汇总 |

### 🤖 AI 智能（6 个）

| # | 工具名 | 功能 | 引擎 |
|---|--------|------|------|
| 7 | `pdooh_audience_insight` | 人群洞察 | ⚡ MiniMax |
| 8 | `pdooh_strategy_suggestion` | 策略建议 | ⚡ MiniMax |
| 9 | `pdooh_media_recommend` | 媒体推荐 | ⚡ MiniMax |
| 10 | `pdooh_scheduling_optimize` | 排期优化 | ⚡ MiniMax |
| 11 | `pdooh_competitor_compare` | 竞品分析 | ⚡ MiniMax |
| 12 | `pdooh_compliance_check` | 合规审核 | ⚡ MiniMax |

### 🎯 投放管理（6 个）

| # | 工具名 | 功能 |
|---|--------|------|
| 13 | `pdooh_create_campaign` | 创建投放计划 |
| 14 | `pdooh_query_campaigns` | 查询投放计划 |
| 15 | `pdooh_submit_creative` | 提交创意物料 |
| 16 | `pdooh_query_report` | 查询效果报告 |
| 17 | `pdooh_update_campaign_status` | 更新投放状态 |
| 18 | `pdooh_query_city_media_types` | 城市媒体类型 |

### 🧠 Tom Agent 方案生成（1 个）

| # | 端点 | 功能 |
|---|------|------|
| 19 | `POST /tom/plan` | 生成投放方案 |

---

## 🚀 一键调用示例

### 1. 查询城市资源汇总

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_city_summary","arguments":{}}'
```

### 2. 查询广州天河区点位

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_screens","arguments":{"city":"广州","district":"天河区","limit":10}}'
```

### 3. 生成投放方案（Tom Agent）

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tom/plan \
  -H "Content-Type: application/json" \
  -d '{"brand":"某品牌","city":"广州","budget":"50万"}'
```

### 4. 人群洞察分析

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_audience_insight","arguments":{"product_desc":"高端白酒","target_city":"广州"}}'
```

### 5. AI 策略建议

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_strategy_suggestion","arguments":{"industry":"白酒","budget":500000,"target_city":"广州"}}'
```

---

## 🐍 Python 调用

```python
import requests

BASE_URL = "http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call"

def call_tool(name, arguments=None):
    """通用 MCP 工具调用"""
    resp = requests.post(BASE_URL, json={
        "name": name,
        "arguments": arguments or {}
    })
    return resp.json()

# 查询城市汇总
result = call_tool("pdooh_query_city_summary")
print(result)

# 查询智能屏
screens = call_tool("pdooh_query_screens", {
    "city": "广州", "district": "天河区", "limit": 10
})
print(screens)

# 人群洞察
insight = call_tool("pdooh_audience_insight", {
    "product_desc": "高端白酒", "target_city": "广州"
})
print(insight)

# AI 策略建议
strategy = call_tool("pdooh_strategy_suggestion", {
    "industry": "白酒", "budget": 500000, "target_city": "广州"
})
print(strategy)
```

---

## 🖥️ Claude Desktop / Cursor MCP 配置

在 Claude Desktop 或 Cursor 的设置文件中添加：

```json
{
  "mcpServers": {
    "pDOOH": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http"],
      "env": {
        "MCP_SERVER_URL": "http://47.253.159.62:5002/api/v2/mcp/pdooh"
      }
    }
  }
}
```

### 配置文件位置

| 客户端 | 配置路径 |
|--------|----------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | 设置 → MCP → 添加服务器 |

---

## 📊 媒体类型与价格

| 媒体类型 | 价格区间 | 单位 |
|----------|----------|------|
| 广告门 | 5,280 - 8,800 元 | 元/面/2周 |
| 单元门 | 980 - 1,180 元 | 元/面/周 |
| 道闸 | 3,000 - 5,000 元 | 元/面/月 |

---

## 🔗 相关链接

| 项目 | 地址 |
|------|------|
| API 文档 | http://47.253.159.62:5002/docs |
| 健康检查 | http://47.253.159.62:5002/api/v2/mcp/pdooh/health |
| 工具列表 | http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/list |
| Skill YAML | http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml |
| 接口解说 | http://duckwolf.cn/pd.html |

---

> ⚠️ **免责声明**：本项目所有语料、数据库及资源均来源于公开渠道或模拟生成，仅供技术研究与学习交流使用。**本软件并非用于商业用途。**
