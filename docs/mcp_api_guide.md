# AIAdPlacer MCP 接口文档

> **版本**: v2.0 | **更新时间**: 2026-06-08 | **数据规模**: 140,000+ 条媒体资源

---

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构](#2-系统架构)
- [3. MCP 接口列表](#3-mcp-接口列表)
- [4. 接口详细说明](#4-接口详细说明)
- [5. 数据表结构](#5-数据表结构)
- [6. 调用示例](#6-调用示例)
- [7. 部署指南](#7-部署指南)

---

## 1. 项目概述

### 1.1 项目简介

AIAdPlacer 是一个户外广告智能投放平台，支持多数据源查询、MCP/A2A 接口供 AI Agent 调用，覆盖道闸、单元门、电梯、LED、智能屏等多种媒体类型。

### 1.2 核心功能

- 📺 多媒体类型查询（道闸、单元门、LED、电梯框架、梯影等）
- 👥 客户数据查询
- 🎯 智能屏资源查询
- 📊 城市资源索引汇总
- 📋 投放计划管理
- ✅ 合规审核
- 🔍 人群洞察分析

### 1.3 数据规模

| 数据类型 | 数量 | 说明 |
|---------|------|------|
| 道闸广告 | 1,021 | 广州道闸点位 |
| 单元门智能框架 | 8,176 | 全国楼盘 |
| 门禁点位 | 66,450 | 全国门禁 |
| 电梯框架 | 19,024 | 全国电梯 |
| 商场 LED | 1,365 | 全国 LED |
| 梯影点位 | 4,327 | 全国梯影 |
| 智能屏 L9 | 9,801 | 27 省 / 100+ 城市 |
| 客户通讯录 | 26,895 | 全国客户 |
| **合计** | **137,000+** | |

---

## 2. 系统架构

### 2.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI + Uvicorn | Python 3.12 |
| 数据库 | PostgreSQL 1 | 主数据存储 |
| 缓存 | Redis 6.2 | 会话 / 缓存 |
| 前端 | React | 可选 |
| 部署 | systemd + Nginx | 服务管理 |

### 2.2 服务端口

| 端口 | 服务 | 地址 |
|------|------|------|
| 5002 | Backend API | `http://47.253.159.62:5002` |
| 3000 | Frontend | `http://47.253.159.62:3000` |
| 80 | Nginx | `http://47.253.159.62` |

### 2.3 MCP 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/mcp/pdooh/health` | GET | 健康检查 |
| `/api/v2/mcp/pdooh/tools/list` | GET | 工具列表 |
| `/api/v2/mcp/pdooh/tools/call` | POST | 工具调用 |

---

## 3. MCP 接口列表

### 3.1 媒体资源类 (10 个)

| # | 工具名称 | 功能 | 数据源 |
|---|---------|------|--------|
| 1 | `pdooh_query_daocha_points` | 道闸广告点位 | `qinlin_daocha_full` |
| 2 | `pdooh_query_smart_frames` | 单元门智能框架 | `qinlin_smart_frames` |
| 3 | `pdooh_query_access_points` | 门禁点位 | `qinlin_access` |
| 4 | `pdooh_query_elevator_frames` | 电梯框架 | `qinlin_elevator_frame` |
| 5 | `pdooh_query_led_points` | 商场 LED | `qinlin_led` |
| 6 | `pdooh_query_shadow_points` | 梯影点位 | `qinlin_shadow` |
| 7 | `pdooh_query_city_resources` | 城市资源索引 | `qinlin_city_index` |
| 8 | `pdooh_query_city_summary` | 城市汇总 | `v_city_media_summary` |
| 9 | `pdooh_query_l9_screens` | 智能屏 L9 | `l9_screens` |
| 10 | ~~`pdooh_query_gtmc_media`~~ | *(已移除)* | — |

### 3.2 客户数据类 (1 个)

| # | 工具名称 | 功能 | 数据源 |
|---|---------|------|--------|
| 11 | `pdooh_query_customers` | 客户通讯录 | `customers_export` |

### 3.3 投放管理类 (7 个)

| # | 工具名称 | 功能 |
|---|---------|------|
| 12 | `pdooh_query_screens` | 媒体资源查询 |
| 13 | `pdooh_get_screen_audience` | 受众分析 |
| 14 | `pdooh_create_campaign` | 创建投放计划 |
| 15 | `pdooh_query_campaigns` | 查询投放计划 |
| 16 | `pdooh_submit_creative` | 提交创意物料 |
| 17 | `pdooh_query_report` | 查询投放报告 |
| 18 | `pdooh_compliance_check` | 合规审核 |
| 19 | `pdooh_audience_insight` | 人群洞察 |

---

## 4. 接口详细说明

### 4.1 `pdooh_query_customers`

**功能**: 查询客户通讯录数据

**参数:**

```json
{
  "brand": "string",       // 品牌名称关键词
  "city": "string",        // 决策城市，如"广州市"
  "industry": "string",    // 行业，如"汽车"、"食品"
  "phone": "string",       // 手机号
  "limit": 50              // 返回数量，默认50
}
```

**返回值:**

```json
{
  "content": [{
    "type": "text",
    "text": "[{...}]"
  }]
}
```

**示例数据:**

```json
{
  "id": 12695,
  "brand": "陶陶居饮食",
  "city": "广州市",
  "industry": "食品",
  "phone": "138xxxx",
  "data": {
    "联系人": "周婉薇",
    "职务": "经理",
    "决策城市": "广州市"
  }
}
```

---

### 4.2 `pdooh_query_l9_screens`

**功能**: 查询智能屏 L9 数据

**参数:**

```json
{
  "city": "string",        // 城市，如"广州市"
  "province": "string",    // 省份，如"广东省"
  "min_price": number,     // 最低楼盘价格（元/㎡）
  "site_name": "string",   // 楼盘名称关键词
  "limit": 50              // 返回数量，默认50
}
```

**示例数据:**

```json
{
  "id": 5456,
  "site_id": 45248,
  "province": "广东省",
  "city": "广州市",
  "district": "天河区",
  "site_name": "骏逸苑",
  "location_name": "大门",
  "property_price": 90326.0,
  "households": 680,
  "terminal_model": "QLG19-C215",
  "mac_address": "FE19EC002082"
}
```

---

### 4.3 `pdooh_query_daocha_points`

**功能**: 查询道闸广告点位

**参数:**

```json
{
  "district": "string",    // 行政区
  "road": "string",        // 道路
  "limit": 50              // 返回数量，默认50
}
```

**示例数据:**

```json
{
  "id": 1,
  "community_name": "XX花园",
  "district": "天河区",
  "road": "天河路",
  "city": "广州",
  "lat": 23.1291,
  "lng": 113.3642,
  "data": {
    "闸数": "2",
    "年价": "12000"
  }
}
```

---

### 4.4 `pdooh_query_city_resources`

**功能**: 查询城市资源索引 — 按城市汇总各媒体类型数量

**参数:**

```json
{
  "city": "string",        // 城市名称，如"广州"
  "media_type": "string",  // 媒体类型筛选
  "limit": 100
}
```

---

### 4.5 `pdooh_query_city_summary`

**功能**: 城市媒体资源汇总 — 按城市聚合统计

**参数:**

```json
{
  "city": "string",        // 城市名称
  "province": "string",    // 省份
  "limit": 100
}
```

---

### 4.6 `pdooh_query_smart_frames`

**功能**: 查询单元门智能框架点位

**参数:**

```json
{
  "city": "string",        // 城市
  "district": "string",    // 区县
  "site_name": "string",   // 楼盘名称
  "limit": 50
}
```

---

### 4.7 `pdooh_query_access_points`

**功能**: 查询门禁点位

**参数:**

```json
{
  "city": "string",
  "district": "string",
  "site_name": "string",
  "limit": 50
}
```

---

### 4.8 `pdooh_query_elevator_frames`

**功能**: 查询电梯框架点位

**参数:**

```json
{
  "city": "string",
  "district": "string",
  "site_name": "string",
  "limit": 50
}
```

---

### 4.9 `pdooh_query_led_points`

**功能**: 查询商场 LED 点位

**参数:**

```json
{
  "city": "string",
  "district": "string",
  "mall_name": "string",   // 商场名称
  "limit": 50
}
```

---

### 4.10 `pdooh_query_shadow_points`

**功能**: 查询梯影点位

**参数:**

```json
{
  "city": "string",
  "district": "string",
  "site_name": "string",
  "limit": 50
}
```

---

### 4.11 `pdooh_create_campaign`

**功能**: 创建投放计划

**参数:**

```json
{
  "name": "string",         // 投放计划名称
  "screen_ids": [1, 2, 3],  // 屏/点位 ID 列表
  "start_date": "2026-06-10",
  "end_date": "2026-06-16",
  "budget": 30000,
  "creative_text": "string"
}
```

---

### 4.12 `pdooh_audience_insight`

**功能**: AI 人群洞察 — 输入品牌/产品描述，自动匹配人群标签和推荐屏列表

**参数:**

```json
{
  "product_desc": "string",  // 产品/品牌描述
  "target_city": "string",   // 目标城市
  "budget_hint": 50000       // 预算提示
}
```

---

### 4.13 `pdooh_compliance_check`

**功能**: 广告内容合规预审（AI 自动审核）

**参数:**

```json
{
  "content": "string",     // 广告文案
  "industry": "string"     // 行业
}
```

---

### 4.14 `pdooh_query_report`

**功能**: 查询投放报告（曝光量 / 开门转化率 / ROI）

**参数:**

```json
{
  "campaign_id": 1,
  "screen_id": 1,
  "start_date": "2026-06-01",
  "end_date": "2026-06-14"
}
```

---

## 5. 数据表结构

### 5.1 核心表一览

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| `qinlin_daocha_full` | 道闸广告点位 | id, community_name, district, road, lat, lng, data |
| `qinlin_smart_frames` | 单元门智能框架 | id, site_name, city, district, lat, lng, households |
| `qinlin_access` | 门禁点位 | id, site_name, city, district, lat, lng, terminal_model |
| `qinlin_elevator_frame` | 电梯框架 | id, site_name, city, district, frames_count |
| `qinlin_led` | 商场 LED | id, mall_name, city, district, led_size, lat, lng |
| `qinlin_shadow` | 梯影点位 | id, site_name, city, district, lat, lng |
| `qinlin_city_index` | 城市资源索引 | id, city, province, media_type, count |
| `v_city_media_summary` | 城市汇总视图 | city, province, total_resources, media_types |
| `l9_screens` | 智能屏 L9 | id, site_id, province, city, district, site_name, property_price |
| `customers_export` | 客户通讯录 | id, brand, city, industry, phone, data |

### 5.2 公共字段约定

所有媒体点位表均包含以下通用字段：

```
id            — 主键 ID
city          — 城市名称
district      — 行政区（如有）
lat           — 纬度
lng           — 经度
site_name     — 楼盘/点位名称
```

---

## 6. 调用示例

### 6.1 基础调用

**健康检查:**

```bash
curl http://47.253.159.62:5002/api/v2/mcp/pdooh/health
```

**获取工具列表:**

```bash
curl http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/list
```

### 6.2 查询客户通讯录

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_query_customers",
    "arguments": {
      "brand": "陶陶居",
      "city": "广州市",
      "industry": "食品",
      "limit": 10
    }
  }'
```

### 6.3 查询智能屏 L9

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_query_l9_screens",
    "arguments": {
      "city": "广州市",
      "province": "广东省",
      "min_price": 50000,
      "limit": 20
    }
  }'
```

### 6.4 查询道闸点位

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_query_daocha_points",
    "arguments": {
      "district": "天河区",
      "limit": 15
    }
  }'
```

### 6.5 创建投放计划

```bash
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pdooh_create_campaign",
    "arguments": {
      "name": "母婴品牌-天河-两周投放",
      "screen_ids": [1, 2, 3],
      "start_date": "2026-06-10",
      "end_date": "2026-06-23",
      "budget": 50000
    }
  }'
```

### 6.6 Python SDK

```python
import requests

BASE_URL = "http://47.253.159.62:5002"
MCP_URL = f"{BASE_URL}/api/v2/mcp/pdooh/tools/call"

def call_tool(name, **kwargs):
    resp = requests.post(MCP_URL, json={"name": name, "arguments": kwargs})
    return resp.json()

# 查询客户
customers = call_tool("pdooh_query_customers", city="广州市", industry="食品", limit=10)

# 查询智能屏
screens = call_tool("pdooh_query_l9_screens", city="广州市", min_price=50000, limit=20)

# 查询道闸
daochoa = call_tool("pdooh_query_daocha_points", district="天河区", limit=15)

# 创建投放计划
campaign = call_tool(
    "pdooh_create_campaign",
    name="母婴品牌-天河投放",
    screen_ids=[1, 2, 3],
    start_date="2026-06-10",
    end_date="2026-06-23",
    budget=50000
)
```

---

## 7. 部署指南

### 7.1 环境要求

- **操作系统**: Linux (推荐 Ubuntu 22.04 / CentOS 7+)
- **Python**: 3.12+
- **数据库**: PostgreSQL 13+
- **缓存**: Redis 6.2+
- **内存**: ≥ 4GB

### 7.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/tomwugdgz/AIAdPlacer.git
cd AIAdPlacer

# 2. 安装依赖
cd backend
pip install -r requirements.txt

# 3. 配置数据库
# 编辑 .env 文件，设置 DATABASE_URL

# 4. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```

### 7.3 生产部署

```bash
# 使用 systemd 管理
sudo cp deploy/aiadplacer.service /etc/systemd/system/
sudo systemctl enable aiadplacer
sudo systemctl start aiadplacer

# Nginx 反代配置
sudo cp deploy/nginx.conf /etc/nginx/conf.d/aiadplacer.conf
sudo nginx -s reload
```

### 7.4 健康检查

```bash
# API 健康检查
curl http://localhost:5002/api/v2/mcp/pdooh/health

# 预期返回
{
  "service": "pDOOH A2A MCP Server",
  "status": "ok",
  "tools_count": 18,
  "mcp_endpoint": "/api/v2/mcp/pdooh/tools/call",
  "skill_endpoint": "/api/v2/mcp/pdooh/skill.yaml"
}
```

---

## 📞 联系 & 支持

> 🌐 在线体验: [duckwolf.cn](http://duckwolf.cn)
>
> 📋 接口解说: [duckwolf.cn/pd.html](http://duckwolf.cn/pd.html)
>
> 🔗 Swagger 文档: [http://47.253.159.62:5002/docs](http://47.253.159.62:5002/docs)
>
> 💬 商务合作: tom@duckwolf.cn

---

**AIAdPlacer** · AI Native pDOOH 投放平台 · Powered by [duckwolf.cn](http://duckwolf.cn)
