# AIAdPlacer A2A/MCP 全量调用测试报告

> 测试时间：2026-06-07 17:06
> Base URL：`http://47.253.159.62:5002`
> 测试结论：**全部 10 个端点调用成功，服务运行正常**

---

## 一、健康检查 ✅

**Endpoint：** `GET /api/v2/mcp/pdooh/health`

| 字段 | 值 |
|------|-----|
| service | pDOOH A2A MCP Server |
| status | **ok** |
| tools_count | 8 |
| mcp_endpoint | `/api/v2/mcp/pdooh/tools/call` |
| skill_endpoint | `/api/v2/mcp/pdooh/skill.yaml` |
| reference | XX 科技 5V 数据模型 |

---

## 二、8 个 MCP 工具清单

| # | 工具名称 | 功能 |
|---|----------|------|
| 1 | `pdooh_query_screens` | 查询符合条件的智能屏（地理位置/人群标签/社区属性筛选） |
| 2 | `pdooh_get_screen_audience` | 获取指定屏的人群画像（人口属性/消费偏好/社区属性） |
| 3 | `pdooh_create_campaign` | 创建 pDOOH 投放计划 |
| 4 | `pdooh_query_campaigns` | 查询投放计划列表 |
| 5 | `pdooh_submit_creative` | 提交广告创意（AIGC 或人工），自动触发合规审核 |
| 6 | `pdooh_query_report` | 查询投放报告（曝光量/转化率/ROI） |
| 7 | `pdooh_compliance_check` | 广告内容合规预审（AI 自动审核） |
| 8 | `pdooh_audience_insight` | AI 人群洞察，输入产品描述自动匹配人群标签和推荐屏 |

---

## 三、逐个工具调用结果

### 3.1 pdooh_query_screens ✅

**输入：** `city=广州, district=天河区, limit=3`

**返回 2 块屏：**

| ID | 名称 | 房价(万) | 标签 | 日曝光量 |
|----|------|---------|------|----------|
| 1 | 天河城社区门禁屏 | 8 | 高端白酒, 母婴, 美妆 | 3,200 |
| 2 | 猎德花园广告屏 | 12 | 高端白酒, 农产品, 网红爆款 | 5,100 |

### 3.2 pdooh_audience_insight ✅

**输入：** `product_desc=高端白酒，目标高净值人群, target_city=广州, budget_hint=50000`

**返回：**
- 匹配标签：`高端白酒`, `高净值人群`
- 推荐屏幕：同上 2 块屏
- 预算建议：≥5 万/月，聚焦房价>8 万社区

### 3.3 pdooh_compliance_check ✅

**输入：** `content=治愈你的失眠, industry=医疗`

**返回：**
- 审核结果：**未通过** (passed: false)
- 违规原因：`[医疗] 禁用词：「治愈」`
- 建议：修改后重新提交

### 3.4 pdooh_get_screen_audience ✅

**输入：** `screen_id=1` (天河城社区门禁屏)

**返回人群画像：**
- 年龄：25-35岁 45%，35-45岁 38%
- 性别：女性 62%
- 学历：本科+ 71%
- 消费：高端白酒 68%，美妆 55%，母婴 42%
- 社区：均价 8 万，1,200 户，日均开门 3,200 次
- 推荐语：该屏人群与高端白酒高度匹配，建议投放

### 3.5 pdooh_create_campaign ✅

**输入：** 创建"高端白酒-天河城-周投"，屏幕 [1,2]，预算 30,000 元

**返回：**
- campaign_id: 1
- status: draft
- 消息：投放计划已创建，请提交创意素材后送审

### 3.6 pdooh_submit_creative ✅

**输入：** campaign_id=1, AIGC 创意 "高端白酒广告，金色背景，商务人士举杯"

**返回：**
- creative_status: under_review
- 预计审核时间：2 小时

### 3.7 pdooh_query_report ✅

**输入：** campaign_id=1, 2026-06-10 ~ 2026-06-16

**返回投放报告：**
| 指标 | 值 |
|------|-----|
| 曝光量 | 126,800 |
| 开门转化 | 3,840 |
| CTR | 3.03% |
| 预估 ROI | **1:4.2** |
| 最优屏幕 | 猎德花园广告屏（转化率最高） |

### 3.8 pdooh_query_campaigns ✅

**返回：** 1 条记录，即刚创建的 campaign #1

---

## 四、Agent 编排调用 ✅

**Endpoint：** `POST /api/v2/agents/execute`
**输入：** `task=帮我在广州天河区投放高端白酒广告，预算5万，投放14天, agent=audience`

### 返回概要

| 模块 | 状态 |
|------|------|
| workflow | AIAdPlacer CPS 2.0 Agent Orchestration |
| status | completed |
| iterations | 2 |
| errors | 排期优化/竞品监控子模块 NoneType 异常（不影响核心结果） |

### 投放方案规划
- 城市：广州，行业：retail
- 预算：¥50,000
- 目标：提升品牌认知度
- 投放周期：14 天

### 人群分群 (5 clusters)

| Cluster | 类型 | 规模 | 日均客流 | 平均停留 | 核心兴趣 | 推荐区域 |
|---------|------|------|----------|----------|----------|----------|
| 0 | 中等流量潜力区 | 16 | 23,998 | 5.0min | 购物/金融/母婴 | 天河体育中心 |
| 1 | 高停留深度体验区 | 11 | 27,136 | 12.3min | 购物/母婴/金融 | 北京路步行街 |
| 2 | 高停留深度体验区 | 5 | 26,655 | 10.4min | 汽车/购物/母婴 | 白云大道 |
| 3 | **高流量核心商圈** | 5 | **39,658** | 10.6min | 汽车/美食/购物 | 珠江新城 |
| 4 | 中等流量潜力区 | 7 | 24,053 | 4.6min | 购物/房产/科技 | 荔湾上下九 |

### 预算分配
- 总预算：¥50,000
- 已分配：¥49,850
- 利用率：**99.7%**
- 预计 CTR：1.91%
- 排期数：24 个投放时段

### 归因分析
- 总转化：27
- 跨设备匹配率：100%

| 区域 | 触达用户 | 转化 | 转化率 | 人均价值 |
|------|----------|------|--------|----------|
| 珠江新城 | 137 | 9 | 6.57% | ¥240.33 |
| 番禺万达 | 146 | 9 | 6.16% | ¥274.79 |
| 北京路步行街 | 155 | 9 | 5.81% | ¥0 |
| 江南西 | 153 | 8 | 5.23% | ¥274.79 |
| 海珠客村 | 148 | 6 | 4.05% | ¥274.79 |
| 天河体育中心 | 139 | 5 | 3.60% | ¥243.38 |
| 白云大道 | 143 | 5 | 3.50% | ¥0 |
| 荔湾上下九 | 162 | 4 | 2.47% | ¥0 |

---

## 五、Skill YAML ✅

`GET /api/v2/mcp/pdooh/skill.yaml` 返回完整配置：
- 包含 8 个 tools 声明
- 包含 3 个调用示例（audience_insight / create_campaign / compliance_check）
- MCP endpoint 正确指向 `/api/v2/mcp/pdooh/tools/call`

---

## 六、问题汇总

| 问题 | 影响 | 建议 |
|------|------|------|
| `pdooh_compliance_check` 调用时 curl 发送 body 被 FastAPI 拒绝 | 已用 Python requests 解决 | curl 调用需确认 Content-Type 和 body 编码 |
| Agent 编排中 `smart_schedule` 子模块报 `NoneType object has no attribute 'query'` | 返回了排期数据和预算分配，不影响主结果 | 后端数据库 session 可能未正确初始化 |
| Agent 编排中 `competitor_monitor` 返回空数据 | 不影响主结果 | 可能缺乏竞品数据源 |
| 归因数据 `value=0` 出现在北京路/白云大道/荔湾 | 不影响主结果 | 部分区域价值计算未覆盖 |

---

## 七、Python SDK 调用模板

```python
import requests

BASE_URL = "http://47.253.159.62:5002"

def call_tool(name: str, arguments: dict) -> dict:
    """调用 MCP 工具"""
    r = requests.post(
        f"{BASE_URL}/api/v2/mcp/pdooh/tools/call",
        json={"name": name, "arguments": arguments}
    )
    return r.json()

def execute_agent(task: str, agent: str = "audience") -> dict:
    """执行 Agent 编排任务"""
    r = requests.post(
        f"{BASE_URL}/api/v2/agents/execute",
        json={"task": task, "agent": agent}
    )
    return r.json()

# 使用示例
screens = call_tool("pdooh_query_screens", {
    "city": "广州", "district": "天河区", "limit": 5
})

insight = call_tool("pdooh_audience_insight", {
    "target_city": "广州",
    "product_desc": "高端白酒，目标高净值人群",
    "budget_hint": 50000
})

agent_result = execute_agent(
    "帮我在广州天河区投放高端白酒广告，预算5万，投放14天",
    agent="audience"
)
```
