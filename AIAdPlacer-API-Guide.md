# AIAdPlacer pDOOH A2A/MCP Server 接口说明文档

## 一、服务器信息

| 项目 | 值 |
|------|-----|
| **服务器** | 阿里云 ECS |
| **公网 IP** | `47.253.159.62` |
| **端口** | `5002` |
| **协议** | HTTP (FastAPI) |
| **框架** | pDOOH A2A MCP Server |
| **API 文档** | `http://47.253.159.62:5002/docs` |
| **健康检查** | `GET /api/v2/mcp/pdooh/health` |

---

## 二、基础 URL

```
BASE_URL = http://47.253.159.62:5002
```

所有接口均基于此 Base URL。

---

## 三、调用方式总览

### 3.1 三种调用模式

| 模式 | 端点 | 用途 | 调用方式 |
|------|------|------|----------|
| **MCP Tool Call** | `POST /api/v2/mcp/pdooh/tools/call` | 调用单个工具 | JSON POST |
| **工具列表** | `GET /api/v2/mcp/pdooh/tools/list` | 获取可用工具列表 | GET |
| **Skill YAML** | `GET /api/v2/mcp/pdooh/skill.yaml` | AI Agent 加载技能定义 | GET |
| **Agent 编排** | `POST /api/v2/agents/execute` | A2A 多 Agent 协作执行 | JSON POST |

### 3.2 MCP Tool Call 标准格式

```
POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call
Content-Type: application/json

{
  "name": "工具名称",
  "arguments": {
    "参数1": "值",
    "参数2": "值"
  }
}
```

**响应格式：**
```json
{
  "content": [ ... ]
}
```

### 3.3 Agent 编排格式

```
POST http://47.253.159.62:5002/api/v2/agents/execute
Content-Type: application/json

{
  "task": "任务描述（自然语言）",
  "agent": "audience|schedule|creative|attribution"
}
```

---

## 四、全部工具清单（15 个）

### 4.1 核心投放工具（8 个）

| # | 工具名 | 说明 | 必填参数 | 选填参数 |
|---|--------|------|----------|----------|
| 1 | `pdooh_query_screens` | 查询智能屏点位 | 无 | city, district, lat, lng, radius, tags, min_house_price, limit |
| 2 | `pdooh_get_screen_audience` | 获取单屏人群画像 | screen_id | - |
| 3 | `pdooh_create_campaign` | 创建投放计划 | name, screen_ids, start_date, end_date, budget | creative_text, ai_generated |
| 4 | `pdooh_query_campaigns` | 查询投放计划列表 | 无 | status, limit |
| 5 | `pdooh_submit_creative` | 提交广告创意 | campaign_id, creative_type | creative_url, ai_prompt |
| 6 | `pdooh_query_report` | 查询投放报告 | 无 | campaign_id, screen_id, start_date, end_date |
| 7 | `pdooh_compliance_check` | 广告合规预审 | content | industry |
| 8 | `pdooh_audience_insight` | AI 人群洞察 | product_desc | target_city, budget_hint |

### 4.2 媒体资源查询工具（7 个）

| # | 工具名 | 说明 | 核心参数 |
|---|--------|------|----------|
| 9 | `pdooh_query_daocha_points` | 道闸广告点位 | district, business_zone, min_car_traffic, limit |
| 10 | `pdooh_query_smart_frames` | 单元门智能框架 | city, district, min_price, limit |
| 11 | `pdooh_query_led_points` | 商场 LED 点位 | city, district, scene, limit |
| 12 | `pdooh_query_elevator_frames` | 电梯框架点位 | city, district, min_price, limit |
| 13 | `pdooh_query_shadow_points` | 梯影点位 | city, resource_type, limit |
| 14 | `pdooh_query_access_points` | 门禁点位 | city, district, min_price, limit |
| 15 | `pdooh_query_city_resources` | 城市资源索引 | city, media_type, limit |
| 16 | `pdooh_query_city_summary` | 城市资源汇总 | 无参数 |

---

## 五、调用示例

### 5.1 Python requests（推荐）

```python
import requests

BASE_URL = "http://47.253.159.62:5002"

# ── 1. 查询智能屏 ──
def query_screens(city="广州", district="天河区", limit=10):
    r = requests.post(f"{BASE_URL}/api/v2/mcp/pdooh/tools/call", json={
        "name": "pdooh_query_screens",
        "arguments": {
            "city": city,
            "district": district,
            "min_house_price": 8,
            "limit": limit
        }
    })
    return r.json()

# ── 2. 创建投放计划 ──
def create_campaign(name, screen_ids, budget, start_date, end_date, creative_text=""):
    r = requests.post(f"{BASE_URL}/api/v2/mcp/pdooh/tools/call", json={
        "name": "pdooh_create_campaign",
        "arguments": {
            "name": name,
            "screen_ids": screen_ids,
            "budget": budget,
            "start_date": start_date,
            "end_date": end_date,
            "creative_text": creative_text
        }
    })
    return r.json()

# ── 3. Agent 编排 ──
def execute_agent(task, agent="audience"):
    r = requests.post(f"{BASE_URL}/api/v2/agents/execute", json={
        "task": task,
        "agent": agent
    })
    return r.json()

# ── 使用示例 ──
screens = query_screens("广州", "天河区")
print(screens)

campaign = create_campaign(
    name="高端白酒-天河城-周投",
    screen_ids=[1, 2],
    budget=30000,
    start_date="2026-06-10",
    end_date="2026-06-16",
    creative_text="品味经典，尊享时刻"
)
print(campaign)

result = execute_agent("帮我在广州天河区投放高端白酒广告，预算5万，投放14天")
print(result)
```

### 5.2 cURL 调用

```bash
# 查询智能屏
curl -s -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_screens","arguments":{"city":"广州","district":"天河区","limit":5}}'

# 合规检查
curl -s -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_compliance_check","arguments":{"content":"治愈你的失眠","industry":"医疗"}}'

# Agent 编排
curl -s -X POST http://47.253.159.62:5002/api/v2/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"帮我在广州天河区投放高端白酒广告，预算5万，投放14天","agent":"audience"}'
```

**⚠️ 注意：** curl 在 Windows PowerShell 下发送 body 可能被 FastAPI 拒绝（`value is not a valid dict`），建议使用 Python `requests` 库调用。

### 5.3 OpenClaw Shell Command

```bash
# 获取 Skill YAML（供 AI Agent 加载）
curl -s http://localhost:5002/api/v2/mcp/pdooh/skill.yaml

# 健康检查
curl -s http://localhost:5002/api/v2/mcp/pdooh/health
```

### 5.4 阿里 OpenClaw 集成

在 OpenClaw 中通过 `execute_shell_command` 调用：

```json
{
  "command": "curl -s -X POST http://localhost:5002/api/v2/mcp/pdooh/tools/call -H 'Content-Type: application/json' -d '{\"name\":\"pdooh_query_screens\",\"arguments\":{\"city\":\"广州\",\"limit\":5}}'"
}
```

> **注意：** 如果 OpenClaw 与 MCP Server 不在同一台机器，需将 `localhost` 替换为 `47.253.159.62`。

---

## 六、各工具详细参数

### 6.1 pdooh_query_screens — 查询智能屏

```json
{
  "name": "pdooh_query_screens",
  "arguments": {
    "city": "广州",
    "district": "天河区",
    "lat": 23.1291,
    "lng": 113.3642,
    "radius": 3000,
    "tags": ["高端白酒", "母婴"],
    "min_house_price": 8,
    "limit": 10
  }
}
```

**返回示例：**
```json
{
  "content": [
    {
      "id": 1,
      "name": "天河城社区门禁屏",
      "city": "广州",
      "district": "天河区",
      "lat": 23.1291,
      "lng": 113.3642,
      "house_price": 8,
      "tags": ["高端白酒", "母婴", "美妆"],
      "impressions_per_day": 3200
    }
  ]
}
```

### 6.2 pdooh_audience_insight — AI 人群洞察

```json
{
  "name": "pdooh_audience_insight",
  "arguments": {
    "product_desc": "高端白酒，目标高净值人群",
    "target_city": "广州",
    "budget_hint": 50000
  }
}
```

**返回：** 匹配的人群标签 + 推荐屏列表 + 预算建议

### 6.3 pdooh_compliance_check — 合规预审

```json
{
  "name": "pdooh_compliance_check",
  "arguments": {
    "content": "治愈你的失眠",
    "industry": "医疗"
  }
}
```

**返回：** 审核结果（通过/不通过）+ 原因说明

### 6.4 pdooh_create_campaign — 创建投放计划

```json
{
  "name": "pdooh_create_campaign",
  "arguments": {
    "name": "高端白酒-天河城-周投",
    "screen_ids": [1, 2, 3],
    "start_date": "2026-06-10",
    "end_date": "2026-06-16",
    "budget": 30000,
    "creative_text": "品味经典，尊享时刻",
    "ai_generated": false
  }
}
```

### 6.5 pdooh_submit_creative — 提交创意

```json
{
  "name": "pdooh_submit_creative",
  "arguments": {
    "campaign_id": 1,
    "creative_type": "aigc",
    "ai_prompt": "高端白酒广告，金色背景，商务人士举杯"
  }
}
```

**creative_type 枚举：** `image` | `video` | `text` | `aigc`

### 6.6 pdooh_query_report — 投放报告

```json
{
  "name": "pdooh_query_report",
  "arguments": {
    "campaign_id": 1,
    "start_date": "2026-06-10",
    "end_date": "2026-06-16"
  }
}
```

**返回：** 曝光量、CTR、ROI 等指标

### 6.7 pdooh_query_daocha_points — 道闸点位

```json
{
  "name": "pdooh_query_daocha_points",
  "arguments": {
    "district": "天河区",
    "min_car_traffic": 10000,
    "limit": 20
  }
}
```

### 6.8 pdooh_query_city_summary — 城市资源汇总

```json
{
  "name": "pdooh_query_city_summary",
  "arguments": {}
}
```

**返回：** 各城市媒体资源总量统计

---

## 七、Agent 编排

### 7.1 支持的 Agent 类型

| Agent | 职责 |
|-------|------|
| `audience` | 人群分群分析、区域推荐 |
| `schedule` | 排期优化、时段分配 |
| `creative` | 创意生成建议 |
| `attribution` | 归因分析、ROI 评估 |

### 7.2 调用示例

```json
{
  "task": "帮我在广州天河区投放高端白酒广告，预算50万，投放14天",
  "agent": "audience"
}
```

**返回示例：**
```json
{
  "workflow": "AIAdPlacer CPS 2.0 Agent Orchestration",
  "status": "completed",
  "iterations": 2,
  "errors": [],
  "plan": "投放方案规划...",
  "audience_insight": {
    "clusters": [
      {
        "cluster_id": 0,
        "cluster_type": "高流量核心商圈",
        "size": 8,
        "avg_foot_traffic": 25000
      }
    ]
  }
}
```

---

## 八、Skill YAML 加载

AI Agent 可通过以下方式自动加载 pDOOH 能力：

```
GET http://47.253.159.62:5002/api/v2/mcp/pdooh/skill.yaml
```

返回内容包含：
- **name:** `pdooh-agent`
- **triggers:** pDOOH / 户外广告投放 / 社区屏 / 程序化户外 等关键词
- **tools:** 全部工具名列表
- **mcp_endpoint:** `/api/v2/mcp/pdooh/tools/call`
- **examples:** 4 个典型调用示例

Agent 匹配到 triggers 关键词时自动加载此 Skill，获得 pDOOH 投放能力。

---

## 九、已知问题 & 注意事项

1. **curl body 问题：** Windows PowerShell 下 curl 发送 JSON body 可能被 FastAPI 拒绝，建议使用 Python `requests` 库
2. **Agent 子模块异常：** 排期优化/竞品监控子模块偶发 `NoneType` 异常，不影响核心返回
3. **归因数据：** 部分区域归因 `value=0`，建议结合多区域数据交叉验证
4. **无认证：** 当前接口无鉴权机制，建议部署时增加 API Key 或 Token 验证
5. **HTTP 明文：** 当前为 HTTP 协议，生产环境建议配置 HTTPS

---

## 十、快速验证命令

```bash
# 一键验证服务是否在线
curl -s http://47.253.159.62:5002/api/v2/mcp/pdooh/health
```

期望返回：
```json
{
  "service": "pDOOH A2A MCP Server",
  "status": "ok",
  "tools_count": 8,
  "mcp_endpoint": "/api/v2/mcp/pdooh/tools/call",
  "skill_endpoint": "/api/v2/mcp/pdooh/skill.yaml"
}
```
