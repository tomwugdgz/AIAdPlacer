# pDOOH 平台 API 完整文档 v2.0

> **文档版本**: v2.0 | **更新时间**: 2026-06-21 | **服务地址**: http://47.253.159.62

---

## 1. 快速开始

### 1.1 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| MCP Server | http://47.253.159.62:5002 | 22个工具 |
| Tom Agent | http://47.253.159.62:5003 | CPM计算 |
| ROI Agent | http://47.253.159.62:5004 | ROI计算 |
| 竞品Agent | http://47.253.159.62:5005 | 竞品监控 |

### 1.2 健康检查

```bash
curl http://47.253.159.62:5002/api/v2/mcp/pdooh/health
```

### 1.3 通用请求格式

```json
{"name": "工具名称", "arguments": {"参数1": "值1"}}
```

---

## 2. MCP Server (5002) - 22个工具

### 工具列表

| # | 工具名称 | 功能 | 分类 |
|---|---------|------|------|
| 1 | pdooh_query_screens | 查询智能屏 | 核心投放 |
| 2 | pdooh_get_screen_audience | 获取屏人群画像 | 核心投放 |
| 3 | pdooh_create_campaign | 创建投放计划 | 核心投放 |
| 4 | pdooh_query_campaigns | 查询投放计划 | 核心投放 |
| 5 | pdooh_submit_creative | 提交创意物料 | 核心投放 |
| 6 | pdooh_query_report | 查询投放报告 | 核心投放 |
| 7 | pdooh_compliance_check | 合规审核 | 核心投放 |
| 8 | pdooh_query_local_screens | 本地智能屏查询 | 本地数据库 |
| 9 | pdooh_query_local_stats | 本地统计查询 | 本地数据库 |
| 10 | pdooh_search_local_community | 本地社区搜索 | 本地数据库 |
| 11 | pdooh_audience_insight | 人群洞察 | AI能力 |
| 12 | pdooh_query_access_points | 门禁点位查询 | 点位查询 |
| 13 | pdooh_query_smart_frames | 单元门点位查询 | 点位查询 |
| 14 | pdooh_query_daocha_points | 道闸点位查询 | 点位查询 |
| 15 | pdooh_query_led_points | 商场LED点位查询 | 点位查询 |
| 16 | pdooh_query_elevator_frames | 电梯框架查询 | 点位查询 |
| 17 | pdooh_query_smart_screen | 智能屏L9查询 | 点位查询 |
| 18 | pdooh_query_shadow_points | 投影点位查询 | 点位查询 |
| 19 | pdooh_query_city_resources | 城市资源统计 | 资源统计 |
| 20 | pdooh_query_city_summary | 全国城市汇总 | 资源统计 |
| 21 | pdooh_query_customers | 客户通讯录查询 | 资源统计 |
| 22 | pdooh_calc_roi | ROI计算 | AI能力 |

---

## 3. 核心投放工具 (7个)

### 3.1 pdooh_query_screens - 查询智能屏点位

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| district | string | 否 | - | 区县名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_screens","arguments":{"city":"广州","limit":10}}'
```

---

### 3.2 pdooh_get_screen_audience - 获取屏人群画像

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| screen_id | string | 是 | 屏ID |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_get_screen_audience","arguments":{"screen_id":"1"}}'
```

**返回示例**:

```json
{
  "screen_id": "1",
  "screen_name": "天河城社区门禁屏",
  "demographics": {
    "age_25_35": "45%",
    "age_35_45": "38%",
    "gender_female": "62%",
    "education_bachelor+": "71%"
  },
  "consumption": {
    "high_end_liquor": "68%",
    "makeup": "55%"
  }
}
```

---

### 3.3 pdooh_create_campaign - 创建投放计划

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 计划名称 |
| screen_ids | array | 是 | 屏ID列表 |
| start_date | string | 是 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 是 | 结束日期 (YYYY-MM-DD) |
| budget | number | 是 | 预算(元) |
| creative_text | string | 否 | 创意文案 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_create_campaign","arguments":{"name":"高端白酒-天河城","screen_ids":[1,2,3],"start_date":"2026-07-01","end_date":"2026-07-07","budget":30000}}'
```

---

### 3.4 pdooh_query_campaigns - 查询投放计划列表

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | - | 状态筛选 (active/paused/completed) |
| limit | integer | 否 | 20 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_campaigns","arguments":{"status":"active","limit":10}}'
```

---

### 3.5 pdooh_submit_creative - 提交创意物料

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| campaign_id | string | 是 | 投放计划ID |
| content | string | 是 | 创意内容 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_submit_creative","arguments":{"campaign_id":"CAMP001","content":"测试广告"}}'
```

---

### 3.6 pdooh_query_report - 查询投放效果报告

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| campaign_id | string | 否 | 投放计划ID |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_report","arguments":{"campaign_id":"CAMP001"}}'
```

---

### 3.7 pdooh_compliance_check - 合规审核

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 广告文案内容 |
| industry | string | 否 | 行业类型 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_compliance_check","arguments":{"content":"广告文案","industry":"食品"}}'
```

---

## 4. 点位查询工具 (7个)

### 4.1 pdooh_query_access_points - 门禁点位查询（广告门）

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| district | string | 否 | - | 区县名称 |
| community | string | 否 | - | 社区名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_access_points","arguments":{"city":"广州","limit":10}}'
```

**返回示例**:

```json
[{"id": 1, "city": "广州", "district": "天河区", "community": "华港花园", "address": "天府路XX号", "media_count": 4}]
```

**数据库信息**: 门禁点位共 66,308 条

---

### 4.2 pdooh_query_smart_frames - 单元门点位查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| district | string | 否 | - | 区县名称 |
| community | string | 否 | - | 社区名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_smart_frames","arguments":{"city":"广州","district":"天河区","limit":10}}'
```

**数据库信息**: 单元门点位共 8,114 条

---

### 4.3 pdooh_query_daocha_points - 道闸点位查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| district | string | 否 | - | 区县名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_daocha_points","arguments":{"city":"广州","limit":10}}'
```

**数据库信息**: 道闸点位共 1,021 条

---

### 4.4 pdooh_query_led_points - 商场LED点位查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| mall_name | string | 否 | - | 商场名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_led_points","arguments":{"city":"广州","limit":10}}'
```

**数据库信息**: 商场LED点位共 1,365 条

---

### 4.5 pdooh_query_smart_screen - 智能屏L9查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| district | string | 否 | - | 区县名称 |
| community | string | 否 | - | 社区名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_smart_screen","arguments":{"city":"广州","limit":10}}'
```

**数据库信息**: 智能屏L9共 9,801 台，分布72个城市

---

### 4.6 pdooh_query_elevator_frames - 电梯框架查询（预留）

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| limit | integer | 否 | 100 | 返回数量 |

**状态**: 预留接口，暂未开放

---

### 4.7 pdooh_query_shadow_points - 投影点位查询（预留）

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| limit | integer | 否 | 100 | 返回数量 |

**状态**: 预留接口，暂未开放

---

## 5. 本地数据库工具 (3个)

### 5.1 pdooh_query_local_screens - 本地智能屏查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| district | string | 否 | - | 区县名称 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_local_screens","arguments":{"city":"广州"}}'
```

---

### 5.2 pdooh_query_local_stats - 本地统计查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 否 | - | 城市名称 |
| media_type | string | 否 | - | 媒体类型 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_local_stats","arguments":{"city":"广州"}}'
```

**返回示例**:

```json
{"city": "广州", "unit_door": 710, "access_door": 2172, "smart_screen": 547, "daocha": 120}
```

---

### 5.3 pdooh_search_local_community - 本地社区搜索

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词 |
| city | string | 否 | - | 城市名称 |
| limit | integer | 否 | 20 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_search_local_community","arguments":{"keyword":"华港花园","city":"广州"}}'
```

---

## 6. 资源统计工具 (3个)

### 6.1 pdooh_query_city_resources - 城市资源统计

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| city | string | 是 | - | 城市名称 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_city_resources","arguments":{"city":"广州"}}'
```

**返回示例**:

```json
{"city": "广州", "unit_door": 710, "access_door": 2172, "smart_screen": 547, "smart_screen_l9": 1228}
```

---

### 6.2 pdooh_query_city_summary - 全国城市汇总

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_city_summary","arguments":{"limit":20}}'
```

**返回示例**:

```json
[{"city": "深圳", "total_points": 921, "rank": 1}, {"city": "重庆", "total_points": 810, "rank": 2}]
```

---

### 6.3 pdooh_query_customers - 客户通讯录查询

**参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 搜索关键词 |
| brand | string | 否 | - | 品牌名称 |
| industry | string | 否 | - | 行业类型 |
| limit | integer | 否 | 100 | 返回数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_query_customers","arguments":{"brand":"麦当劳","limit":10}}'
```

**数据库信息**: 客户通讯录共 26,895 条

---

## 7. AI能力工具 (2个)

### 7.1 pdooh_audience_insight - 人群洞察

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市名称 |
| district | string | 否 | 区县名称 |
| community | string | 否 | 社区名称 |
| media_type | string | 否 | 媒体类型 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_audience_insight","arguments":{"city":"广州","district":"天河区"}}'
```

---

### 7.2 pdooh_calc_roi - ROI计算

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| brand | string | 是 | 品牌名称 |
| frames | integer | 是 | 投放框数 |
| period_weeks | integer | 是 | 投放周期(周) |
| plan_type | string | 否 | 方案类型 (A/B/C) |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"pdooh_calc_roi","arguments":{"brand":"黑人牙膏","frames":5000,"period_weeks":2,"plan_type":"A"}}'
```

**返回示例**:

```json
{"brand": "黑人牙膏", "frames": 5000, "period_weeks": 2, "pessimistic_roi": "21%", "neutral_roi": "61%", "optimistic_roi": "173%"}
```

---

## 8. Tom Agent (5003) - CPM计算

### 8.1 服务信息

| 项目 | 值 |
|------|-----|
| 地址 | http://47.253.159.62:5003 |
| 版本 | v2.0 |
| 功能 | 智能户外广告投放方案生成 |

### 8.2 API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| /health | GET | 健康检查 |
| /api/prompt | GET | 系统提示词 |
| /api/query/points | POST | 查询点位 |
| /api/query/city | GET | 城市资源统计 |
| /api/plan/generate | POST | 生成投放方案 |
| /api/cpm/track | POST | CPM跟踪计算 |
| /api/cpm/compare | POST | CPM对比计算 |

### 8.3 投放方案生成

**端点**: POST /api/plan/generate

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| brand | string | 是 | 品牌名称 |
| budget | string | 是 | 预算(如: 30万) |
| city | string | 否 | 城市名称 |
| industry | string | 否 | 行业类型 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5003/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{"brand":"比亚迪","budget":"30万","city":"广州"}'
```

**返回示例**:

```json
{"brand": "比亚迪", "budget": "30万", "media_mix": {"unit_door": "40%", "access_door": "30%", "smart_screen": "15%", "app": "15%"}, "cpm": "7.5元/千人", "total_reach": "450万人次"}
```

---

### 8.4 CPM跟踪计算

**端点**: POST /api/cpm/track

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市名称 |
| media_type | string | 是 | 媒体类型 (unit_door/access_door/smart_screen) |
| weeks | integer | 是 | 投放周期(周) |
| limit | integer | 否 | 点位数量 |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5003/api/cpm/track \
  -H "Content-Type: application/json" \
  -d '{"city":"广州","media_type":"unit_door","weeks":2,"limit":100}'
```

**返回示例**:

```json
{"city": "广州", "media_type": "unit_door", "frames": 1002, "uv": 213996, "pv": 2091194, "cost": 30060, "cpm": "7.17元/千人"}
```

---

### 8.5 CPM对比计算

**端点**: POST /api/cpm/compare

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| unit_qty | integer | 是 | 单元门数量 |
| access_qty | integer | 是 | 广告门数量 |
| weeks | integer | 是 | 投放周期(周) |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5003/api/cpm/compare \
  -H "Content-Type: application/json" \
  -d '{"unit_qty":100,"access_qty":50,"weeks":2}'
```

**返回示例**:

```json
{"unit_door": {"cpm": "7.17元/千人"}, "access_door": {"cpm": "2.73元/千人"}, "combined": {"cpm": "3.10元/千人"}}
```

---

## 9. ROI Agent (5004) - ROI计算

### 9.1 服务信息

| 项目 | 值 |
|------|-----|
| 地址 | http://47.253.159.62:5004 |
| 版本 | v2.0 |
| 功能 | 社区精准营销ROI计算 |

### 9.2 API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| /health | GET | 健康检查 |
| /api/roi | POST | ROI三场景计算 |
| /api/compare | GET | 行业ROI对比 |
| /api/formula | GET | 公式说明 |

### 9.3 ROI计算

**端点**: POST /api/roi

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| frames | integer | 是 | 投放框数 |
| period_weeks | integer | 是 | 投放周期(周) |
| plan_type | string | 否 | 方案类型 (A/B/C) |

**调用示例**:

```bash
curl -X POST http://47.253.159.62:5004/api/roi \
  -H "Content-Type: application/json" \
  -d '{"frames":5000,"period_weeks":2,"plan_type":"A"}'
```

**返回示例**:

```json
{
  "frames": 5000,
  "period_weeks": 2,
  "cost": 150000,
  "scenarios": {
    "pessimistic": {"roi": "21%", "extra_sales": 315000},
    "neutral": {"roi": "61%", "extra_sales": 615000},
    "optimistic": {"roi": "173%", "extra_sales": 1155000}
  }
}
```

---

### 9.4 ROI三场景说明

| 场景 | 记忆率 | 客单价 | ROI |
|------|--------|--------|-----|
| 悲观 | 15% | 20元 | 21% |
| 中性 | 18% | 22元 | 61% |
| 乐观 | 22% | 25元 | 173% |

### 9.5 支持行业分类

- 日化用品、食品饮料、母婴用品、美妆护肤
- 家电数码、汽车用品、医药保健、餐饮连锁、通用

---

## 10. 竞品Agent (5005) - 竞品监控

### 10.1 服务信息

| 项目 | 值 |
|------|-----|
| 地址 | http://47.253.159.62:5005 |
| 版本 | v2.0 |
| 功能 | 竞品数据库、市场情报、品牌动态 |

### 10.2 API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| /health | GET | 健康检查 |
| /api/competitors | GET | 竞品列表 |
| /api/pricing | GET | 竞品定价 |
| /api/compare | GET | 竞品对比 |
| /api/intelligence | GET | 市场情报 |
| /api/intelligence/stats | GET | 情报统计 |
| /api/intelligence/search | GET | 搜索情报 |
| /api/industries | GET | 行业分类 |
| /api/brands | GET | 重点品牌 |

### 10.3 竞品列表

**端点**: GET /api/competitors

**调用示例**:

```bash
curl http://47.253.159.62:5005/api/competitors
```

**返回示例**:

```json
[{"name": "分众传媒", "media_type": "电梯媒体", "coverage": "200+城市"}, {"name": "新潮传媒", "media_type": "社区媒体", "coverage": "100+城市"}]
```

---

### 10.4 市场情报

**端点**: GET /api/intelligence

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| industry | string | 否 | 行业类型 |
| brand | string | 否 | 品牌名称 |
| format | string | 否 | 返回格式 (json/list) |

**调用示例**:

```bash
curl 'http://47.253.159.62:5005/api/intelligence?industry=汽车&format=list'
```

**返回示例**:

```json
[{"title": "比亚迪秦L上市", "brand": "比亚迪", "date": "2026-06-20", "summary": "比亚迪发布新款车型"}]
```

---

### 10.5 情报搜索

**端点**: GET /api/intelligence/search

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |

**调用示例**:

```bash
curl 'http://47.253.159.62:5005/api/intelligence/search?q=麦当劳'
```

---

### 10.6 行业分类 (14个)

快消、日化、汽车、科技、零售、餐饮、教育、文旅、家电、母婴、美妆、通讯、酒水、饮料

### 10.7 重点品牌 (30+)

麦当劳、肯德基、瑞幸咖啡、比亚迪、小鹏汽车、广汽丰田、腾讯、阿里、京东、小米、美的、格力、中国移动、中国电信等

---

## 11. MCP Skill 配置

### 11.1 Skill YAML 配置

将以下内容保存为 `pdooh-mcp-skill.yaml`:

```yaml
name: pdooh-mcp
description: pDOOH 程序化户外广告 MCP 接口 Skill
version: "2.0"
endpoint: http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call
tools:
  - pdooh_query_screens
  - pdooh_get_screen_audience
  - pdooh_create_campaign
  - pdooh_query_campaigns
  - pdooh_submit_creative
  - pdooh_query_report
  - pdooh_compliance_check
  - pdooh_query_local_screens
  - pdooh_query_local_stats
  - pdooh_search_local_community
  - pdooh_audience_insight
  - pdooh_query_access_points
  - pdooh_query_smart_frames
  - pdooh_query_daocha_points
  - pdooh_query_led_points
  - pdooh_query_elevator_frames
  - pdooh_query_smart_screen
  - pdooh_query_shadow_points
  - pdooh_query_city_resources
  - pdooh_query_city_summary
  - pdooh_query_customers
  - pdooh_calc_roi
```

### 11.2 Python SDK 使用

```python
import requests

BASE_URL = "http://47.253.159.62:5002"

def call_mcp_tool(name, **kwargs):
    resp = requests.post(
        f"{BASE_URL}/api/v2/mcp/pdooh/tools/call",
        json={"name": name, "arguments": kwargs}
    )
    return resp.json()

# 查询智能屏
screens = call_mcp_tool("pdooh_query_screens", city="广州", limit=10)

# 创建投放计划
campaign = call_mcp_tool(
    "pdooh_create_campaign",
    name="高端白酒-天河城",
    screen_ids=[1, 2, 3],
    start_date="2026-07-01",
    end_date="2026-07-07",
    budget=30000
)

# 计算ROI
roi = call_mcp_tool("pdooh_calc_roi", brand="黑人牙膏", frames=5000, period_weeks=2)
```

### 11.3 JavaScript/Node.js SDK

```javascript
const axios = require('axios');

const BASE_URL = 'http://47.253.159.62:5002';

async function callMcpTool(name, args = {}) {
  const resp = await axios.post(`${BASE_URL}/api/v2/mcp/pdooh/tools/call`, {
    name,
    arguments: args
  });
  return resp.data;
}

// 查询智能屏
const screens = await callMcpTool('pdooh_query_screens', { city: '广州', limit: 10 });

// 创建投放计划
const campaign = await callMcpTool('pdooh_create_campaign', {
  name: '高端白酒-天河城',
  screen_ids: [1, 2, 3],
  start_date: '2026-07-01',
  end_date: '2026-07-07',
  budget: 30000
});
```

---

## 12. 价格配置

### 12.1 成交价格（成本底价）

| 媒体类型 | 单价 | 周期 | 说明 |
|---------|------|------|------|
| 单元门 | 20元/面 | 周 | 现金底价 |
| 广告门 | 125元/面 | 周 | 现金底价 |
| 智能屏 | 2元/台 | 周 | 现金底价 |
| 开门App | 50,000元/周 | 周 | App推送 |

### 12.2 刊例价格

| 媒体类型 | 核心城市 | 重点城市 | 周期 |
|---------|---------|---------|------|
| 单元门 | 1,180元/面 | 980元/面 | 周 |
| 广告门 | 5,280元/面 | 4,680元/面 | 2周 |

### 12.3 置换价格

| 媒体类型 | 单价 | 周期 | 说明 |
|---------|------|------|------|
| 单元门 | 65元/面 | 周 | 置换报价 |
| 广告门 | 500元/面 | 周 | 置换报价 |
| 智能屏 | 51.8元/台 | 周 | 置换报价 |
| App内页 | 12.6万元/周 | 周 | 置换报价 |

---

## 13. 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| 200 | 成功 | - |
| 400 | 参数错误 | 检查请求参数 |
| 401 | 认证失败 | 检查API配置 |
| 404 | 资源不存在 | 检查城市/社区名称 |
| 500 | 服务器错误 | 联系技术支持 |
| 503 | 服务不可用 | 检查服务状态 |

---

## 14. 常见问题

**Q1: 如何查询特定城市的点位？**
使用 `pdooh_query_access_points` 或 `pdooh_query_smart_frames`，传入 city 参数。

**Q2: CPM计算结果不准确？**
确认传入的 media_type 参数正确，并检查 weeks 参数是否为整数。

**Q3: 如何获取ROI计算结果？**
使用 `pdooh_calc_roi` 工具，传入品牌、框数、周期参数。

**Q4: 支持哪些城市？**
目前支持全国 217+ 城市，包括北上广深及重点城市。

**Q5: 如何联系技术支持？**
联系 Tom: 17665188615

---

**文档结束**

**最后更新**: 2026-06-21
**版本**: v2.0
