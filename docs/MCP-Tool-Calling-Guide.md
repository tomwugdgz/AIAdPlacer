# pDOOH MCP 工具调用手册

**版本**：v2.1  
**更新日期**：2026-06-16  
**服务地址**：`http://47.253.159.62:5002`  
**数据规模**：门禁 66,308 条 · 单元门 8,114 条 · 智能屏 4,488 条 · 联系人 26,895 条

---

## 目录

1. [快速开始](#1-快速开始)
2. [完整工具清单](#2-完整工具清单)
3. [核心投放工具](#3-核心投放工具详解)
4. [AI 能力工具](#4-ai-能力工具详解)
5. [媒体资源工具](#5-媒体资源工具详解)
6. [客户查询工具](#6-客户查询工具详解)
7. [Python 调用示例](#7-python-调用示例)
8. [错误处理](#8-错误处理)
9. [数据规模说明](#9-数据规模说明)
10. [快速查询命令](#10-快速查询命令)

---

## 1. 快速开始

### 1.1 服务状态检查

在调用任何工具前，建议先检查服务健康状态：

```bash
curl http://47.253.159.62:5002/api/v2/mcp/pdooh/health
```

**响应示例**：

```json
{
  "service": "pDOOH A2A MCP Server",
  "status": "ok",
  "version": "v2.0",
  "tools_count": 22,
  "data_summary": {
    "access_points": 66308,
    "smart_frames": 8114,
    "screens": 4488,
    "customers": 26895
  }
}
```

### 1.2 通用调用格式

所有工具通过同一个端点调用：

**POST** `http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call`

**请求头**：`Content-Type: application/json`

**请求体**：

```json
{
  "name": "工具名称",
  "arguments": {
    "参数1": "值1",
    "参数2": "值2"
  }
}
```

**Python 通用封装**：

```python
import requests

BASE_URL = "http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call"

def call_tool(name: str, arguments: dict) -> dict:
    """通用 MCP 工具调用函数"""
    resp = requests.post(
        BASE_URL,
        json={"name": name, "arguments": arguments},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()
```

---

## 2. 完整工具清单

共 **22 个工具**，按功能分为 4 大类：

| 类别 | 工具名称 | 功能说明 |
|------|----------|----------|
| **核心投放** | `pdooh_query_screens` | 查询智能屏点位 |
| | `pdooh_create_campaign` | 创建投放计划 |
| | `pdooh_query_campaigns` | 查询投放计划列表 |
| | `pdooh_query_report` | 查询投放效果报告 |
| | `pdooh_check_compliance` | 广告文案合规检查 |
| **AI 能力** | `pdooh_ai_audience_insight` | AI 人群洞察分析 |
| | `pdooh_ai_local_screens` | 本地化点位推荐 |
| | `pdooh_ai_stats` | AI 驱动统计分析 |
| | `pdooh_ai_search` | 自然语言语义搜索 |
| | `pdooh_ai_smart_frames` | AI 广告框架生成 |
| **媒体资源** | `pdooh_query_access_points` | 查询门禁点位 |
| | `pdooh_query_smart_frames` | 查询单元门点位 |
| | `pdooh_query_daocha_points` | 查询道闸点位 |
| | `pdooh_query_city_resources` | 城市媒体资源统计 |
| | `pdooh_query_city_summary` | 全国城市资源汇总 |
| **客户查询** | `pdooh_query_customers` | 查询客户通讯录 |

---

## 3. 核心投放工具详解

### 3.1 pdooh_query_screens — 查询智能屏点位

查询符合条件的智能屏点位，支持地理位置、人群标签、房价等多维度筛选。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `city` | string | 否 | 城市名称 | `"广州"` |
| `district` | string | 否 | 区县名称 | `"天河区"` |
| `lat` | number | 否 | 纬度（WGS84） | `23.1291` |
| `lng` | number | 否 | 经度（WGS84） | `113.2644` |
| `radius` | number | 否 | 搜索半径（米） | `3000` |
| `tags` | array[string] | 否 | 人群标签 | `["母婴","高消费"]` |
| `min_house_price` | number | 否 | 最低房价（万元） | `50000` |
| `limit` | integer | 否 | 返回数量上限（默认20） | `10` |

**调用示例 1：按城市查询**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_screens", "arguments": {"city": "广州", "limit": 5}}'
```

**调用示例 2：按坐标+半径查询**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_screens", "arguments": {"lng": 113.2644, "lat": 23.1291, "radius": 5000}}'
```

**调用示例 3：筛选高净值社区**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_screens", "arguments": {"city": "广州", "min_house_price": 50000}}'
```

**调用示例 4：按人群标签筛选**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_screens", "arguments": {"city": "广州", "tags": ["母婴", "高消费"], "limit": 10}}'
```

---

### 3.2 pdooh_create_campaign — 创建投放计划

创建 pDOOH 广告投放计划，返回计划 ID。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 投放计划名称 |
| `screen_ids` | array[integer] | ✅ | 智能屏 ID 列表 |
| `start_date` | string | ✅ | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | string | ✅ | 结束日期，格式 `YYYY-MM-DD` |
| `budget` | number | ✅ | 总预算（人民币元） |
| `creative_text` | string | 否 | 广告文案内容 |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_create_campaign",
    "arguments": {
      "name": "广州天河母婴品牌6月投放",
      "screen_ids": [12345, 12346, 12347],
      "start_date": "2026-06-20",
      "end_date": "2026-07-20",
      "budget": 50000,
      "creative_text": "XX品牌，全场5折！"
    }
  }'
```

---

### 3.3 pdooh_query_campaigns — 查询投放计划

查询已创建的投放计划列表，支持按状态筛选。

**参数说明**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `status` | string | 计划状态：`draft` / `running` / `paused` / `completed` |
| `limit` | integer | 返回数量上限（默认 20） |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_campaigns", "arguments": {"status": "running", "limit": 10}}'
```

---

### 3.4 pdooh_query_report — 查询投放报告

查询指定投放计划的效果数据，包括曝光量、点击率、OTC 等指标。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `campaign_id` | integer | ✅ | 投放计划 ID |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_report", "arguments": {"campaign_id": 12345}}'
```

---

### 3.5 pdooh_check_compliance — 合规检查

检查广告文案是否符合广告法及平台投放规范，返回合规建议。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | 待检查广告文案 |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_check_compliance", "arguments": {"text": "全场最低价，销量第一"}}'
```

---

## 4. AI 能力工具详解

### 4.1 pdooh_ai_audience_insight — 人群洞察

AI 分析目标人群特征，生成精准投放建议，包括推荐标签、推荐区域、媒体组合比例等。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `description` | string | ✅ | 品牌/产品描述 |
| `city` | string | 否 | 目标城市（不填则全国） |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_ai_audience_insight", "arguments": {"description": "高端婴幼儿奶粉品牌", "city": "广州"}}'
```

**响应示例**：

```json
{
  "target_tags": ["高收入家庭", "母婴", "25-35岁女性"],
  "recommended_districts": ["天河区", "海珠区", "越秀区"],
  "recommended_media_mix": {
    "unit_door": 0.4,
    "access_door": 0.4,
    "smart_screen": 0.2
  },
  "estimated_reach": "50万+ 人群",
  "suggested_budget": "50000-80000元"
}
```

---

### 4.2 pdooh_ai_local_screens — 本地化推荐

根据品牌特征和指定城市，AI 推荐最优本地化投放方案。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `brand` | string | ✅ | 品牌名称 |
| `city` | string | ✅ | 目标城市 |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_ai_local_screens", "arguments": {"brand": "农夫山泉", "city": "广州"}}'
```

---

### 4.3 pdooh_ai_stats — 统计分析

AI 驱动的统计分析工具，支持多维度数据聚合与趋势分析。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `metric` | string | ✅ | 统计指标，如 `screens_by_city`、`reach_by_district` |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_ai_stats", "arguments": {"metric": "screens_by_city"}}'
```

---

### 4.4 pdooh_ai_search — 语义搜索

基于自然语言描述的语义搜索，AI 理解意图并返回最相关点位。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 自然语言搜索查询 |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_ai_search", "arguments": {"query": "天河区高收入社区附近的智能屏"}}'
```

---

### 4.5 pdooh_ai_smart_frames — 智能框架生成

AI 根据品牌和创意主题，自动生成广告框架内容和排版建议。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `brand` | string | ✅ | 品牌名称 |
| `theme` | string | ✅ | 创意主题 |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_ai_smart_frames", "arguments": {"brand": "农夫山泉", "theme": "天然健康"}}'
```

---

## 5. 媒体资源工具详解

### 5.1 pdooh_query_access_points — 查询门禁点位

查询社区门禁广告点位，含楼盘名称、房价、户数等社区信息。

**参数说明**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `city` | string | 城市名称 |
| `district` | string | 区县名称 |
| `limit` | integer | 返回数量上限（默认 20） |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_access_points", "arguments": {"city": "广州", "limit": 10}}'
```

**返回字段说明**：

| 字段 | 说明 |
|------|------|
| `id` | 点位 ID |
| `city` / `district` | 地理位置 |
| `community_name` | 楼盘/小区名称 |
| `device_type` | 门禁设备类型 |
| `lng` / `lat` | WGS84 坐标 |
| `house_price` | 房价（万元/㎡） |
| `households` | 小区户数 |
| `buildings` | 楼栋数 |

---

### 5.2 pdooh_query_smart_frames — 查询单元门点位

查询单元门智能框架点位，适合社区精准触达场景。

**参数说明**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `city` | string | 城市名称 |
| `district` | string | 区县名称 |
| `limit` | integer | 返回数量上限（默认 20） |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_smart_frames", "arguments": {"city": "广州", "limit": 10}}'
```

---

### 5.3 pdooh_query_daocha_points — 查询道闸点位

查询停车场道闸广告点位，适合车主人群触达。

**参数说明**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `city` | string | 城市名称 |
| `limit` | integer | 返回数量上限（默认 20） |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_daocha_points", "arguments": {"city": "广州", "limit": 10}}'
```

---

### 5.4 pdooh_query_city_resources — 城市资源统计

查询指定城市的各类媒体资源统计数据。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `city` | string | ✅ | 城市名称 |

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_city_resources", "arguments": {"city": "广州"}}'
```

**响应示例**：

```json
{
  "city": "广州",
  "access_points": 2174,
  "smart_frames": 710,
  "screens": 4488,
  "daocha": 45,
  "coverage": {
    "districts": 11,
    "buildings": 1500,
    "households": 500000
  }
}
```

---

### 5.5 pdooh_query_city_summary — 全国城市汇总

查询全国所有覆盖城市的资源汇总数据。

**调用示例**：

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_city_summary", "arguments": {}}'
```

---

## 6. 客户查询工具详解

### 6.1 pdooh_query_customers — 查询客户资料

查询客户通讯录数据库（26,895 条记录），支持按品牌、行业、城市等多维度筛选。

**数据说明**：覆盖全国主要广告主决策人信息，含联系人姓名、职务、联系方式等。

**参数说明**：

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `brand` | string | 品牌名称（模糊匹配） | `"小鹏汽车"` |
| `contact` | string | 联系人姓名/职务 | `"张总"` / `"CMO"` |
| `industry` | string | 行业 | `"汽车"` |
| `city` | string | 决策城市 | `"广州"` |
| `limit` | integer | 返回数量上限（默认 20） | `10` |

**调用示例 1：按品牌搜索**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_customers", "arguments": {"brand": "小鹏汽车", "limit": 5}}'
```

**调用示例 2：按行业搜索**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_customers", "arguments": {"industry": "汽车", "limit": 10}}'
```

**调用示例 3：按联系人职务搜索**

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_customers", "arguments": {"contact": "CMO", "limit": 10}}'
```

**返回字段说明**：

| 字段 | 说明 |
|------|------|
| `客户简称` | 品牌简称 |
| `品牌名称` | 完整品牌名 |
| `决策城市` | 总部/决策所在地 |
| `行业` | 所属行业 |
| `联系人` | 决策人姓名 |
| `部门` | 所在部门 |
| `职务` | 职位 |
| `手机` | 联系电话 |
| `座机` | 座机号码 |

---

## 7. Python 调用示例

### 7.1 安装依赖

```bash
pip install requests
```

### 7.2 完整调用示例

```python
import requests
from typing import Dict, Any, Optional

BASE_URL = "http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call"

def call_tool(name: str, arguments: Dict[str, Any]) -> Optional[Dict]:
    """通用 MCP 工具调用函数（带异常处理）"""
    try:
        resp = requests.post(
            BASE_URL,
            json={"name": name, "arguments": arguments},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"调用失败 [{name}]: {e}")
        return None

# === 示例1：查询智能屏点位 ===
result = call_tool("pdooh_query_screens", {
    "city": "广州",
    "min_house_price": 50000,
    "limit": 10
})
if result:
    print(f"找到 {len(result.get('screens', []))} 个高净值社区点位")

# === 示例2：查询客户资料 ===
result = call_tool("pdooh_query_customers", {
    "industry": "汽车",
    "limit": 5
})
if result:
    for customer in result.get("customers", []):
        print(f"品牌: {customer['品牌名称']}, 联系人: {customer['联系人']}")

# === 示例3：创建投放计划 ===
result = call_tool("pdooh_create_campaign", {
    "name": "广州天河母婴品牌6月投放",
    "screen_ids": [12345, 12346, 12347],
    "start_date": "2026-06-20",
    "end_date": "2026-07-20",
    "budget": 50000,
    "creative_text": "XX品牌，全场5折！"
})
if result:
    print(f"投放计划已创建，ID: {result.get('campaign_id')}")
```

---

## 8. 错误处理

### 8.1 常见错误码

| HTTP 状态码 | 说明 | 解决方案 |
|-------------|------|----------|
| `400` | 请求参数错误 | 检查参数类型和必填字段 |
| `404` | 工具不存在 | 核对工具名称拼写 |
| `500` | 服务内部错误 | 联系技术支持 |
| `timeout` | 请求超时 | 增大 timeout 或重试 |

### 8.2 带重试的调用封装

```python
import requests
from typing import Optional, Dict, Any

BASE_URL = "http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call"

def safe_call_tool(
    name: str,
    arguments: Dict[str, Any],
    retries: int = 3,
    timeout: int = 30
) -> Optional[Dict]:
    """
    带重试机制的 MCP 工具调用
    """
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                BASE_URL,
                json={"name": name, "arguments": arguments},
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[{attempt}/{retries}] HTTP {resp.status_code}: {resp.text[:200]}")
        except requests.exceptions.Timeout:
            print(f"[{attempt}/{retries}] 请求超时")
        except Exception as e:
            print(f"[{attempt}/{retries}] 异常: {e}")

        if attempt < retries:
            import time
            time.sleep(1)  # 简单退避

    print("所有重试均失败")
    return None
```

---

## 9. 数据规模说明

| 数据类型 | 记录数 | 覆盖范围 | 更新频率 |
|----------|---------|----------|----------|
| 门禁点位 | 66,308 条 | 全国主要城市 | 月度更新 |
| 单元门点位 | 8,114 条 | 智能框架网络 | 月度更新 |
| 智能屏 | 4,488 条 | 带 GPS 坐标 | 实时更新 |
| 道闸点位 | 1,021 条 | 停车场网络 | 季度更新 |
| 客户通讯录 | 26,895 条 | 全国广告主决策人 | 季度更新 |

---

## 10. 快速查询命令

### 10.1 健康检查

```bash
curl http://47.253.159.62:5002/api/v2/mcp/pdooh/health
```

### 10.2 查询广州门禁点位（前20条）

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_access_points", "arguments": {"city": "广州", "limit": 20}}'
```

### 10.3 查询广州城市资源统计

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_city_resources", "arguments": {"city": "广州"}}'
```

### 10.4 查询汽车行业客户（前20条）

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_customers", "arguments": {"industry": "汽车", "limit": 20}}'
```

---

## 11. 相关服务

### ROI Agent（独立服务）

MCP 工具服务专注于媒体资源查询和投放管理，ROI 计算由独立的 ROI Agent 提供服务：

- **服务地址**：`http://47.253.159.62:5004`
- **功能说明**：投放 ROI 测算、品类参数查询、三方案对比
- **调用手册**：请参阅 `docs/ROI-Agent-User-Guide.md`

---

## 12. 联系方式

| 事项 | 信息 |
|------|------|
| 商务咨询 | Tom `17665188615` |
| 媒体方 | 亲邻传媒 |
| 技术支持 | 通过商务联系人转接 |

---

*最后更新：2026-06-16*
