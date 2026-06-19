# pDOOH Client

Python 客户端库，用于调用 pDOOH API（MCP Server、Tom Agent、ROI Agent、竞品 Agent）。

让用户可以通过 Python 直接调用所有 pDOOH 接口，支持任何电脑安装和使用。

## ✨ 功能特性

- ✅ **完整封装**：封装 4 个服务的所有 API（MCP/Tom Agent/ROI Agent/竞品 Agent）
- ✅ **简洁接口**：统一的 `PDOOHClient` 入口类，一个客户端调用所有服务
- ✅ **类型标注**：完整的 type hints，支持 IDE 自动补全
- ✅ **中文文档**：详细的中文 docstring，降低学习成本
- ✅ **异常处理**：自定义异常类，区分不同类型的错误
- ✅ **单元测试**：覆盖核心功能（mock HTTP 请求）

## 📦 安装

```bash
pip install pdooh-client
```

或者从源码安装：

```bash
git clone https://github.com/tomwugdgz/AIAdPlacer.git
cd AIAdPlacer/pdooh_client
pip install -e .
```

## 🚀 快速开始

```python
from pdooh_client import PDOOHClient

# 创建客户端
client = PDOOHClient(base_url="http://47.253.159.62")

# 查询智能屏
screens = client.mcp.query_screens(city="广州", limit=10)

# 计算 ROI
roi_result = client.roi.calc_roi(
    frames=1000,
    period_weeks=2,
    category="日化用品",
    media_type="unit_door",
    price_type="exchange"
)

# 生成方案
plan = client.tom.generate_plan(
    brand="比亚迪",
    budget="30万",
    city="广州",
    industry="汽车"
)

# 查询竞品
competitors = client.competitor.get_competitors()
```

## 📚 API 文档

### MCP Server (22 个工具)

#### 1.1 核心投放工具 (7个)
- `query_screens(city, district, ...)` - 查询智能屏
- `get_screen_audience(screen_id)` - 获取屏人群画像
- `create_campaign(name, budget, ...)` - 创建投放计划
- `query_campaigns(status, ...)` - 查询投放计划
- `submit_creative(campaign_id, ...)` - 提交创意
- `query_report(campaign_id)` - 查询投放报告
- `compliance_check(content)` - 合规审核

#### 1.2 本地数据库工具 (4个)
- `query_local_screens(city, ...)` - 查询本地屏幕
- `query_local_stats()` - 查询本地统计
- `search_local_community(keyword)` - 搜索楼盘
- `audience_insight(city, ...)` - AI人群洞察

#### 1.3 点位查询工具 (7个)
- `query_access_points(city, ...)` - 查询门禁点位
- `query_smart_frames(city, ...)` - 查询单元门点位
- `query_daocha_points(city, ...)` - 查询道闸点位
- `query_led_points(city, ...)` - 查询LED点位
- `query_elevator_frames(city, ...)` - 查询电梯框架
- `query_smart_screen_2025(city, ...)` - 查询智能屏2025数据
- `query_shadow_points(city, ...)` - 查询投影屏点位

#### 1.4 资源统计工具 (3个)
- `query_city_resources(city)` - 查询城市资源统计
- `query_city_summary()` - 查询全国城市汇总
- `query_customers()` - 查询客户资料

#### 1.5 ROI计算工具 (1个)
- `calc_roi(frames, period_weeks, ...)` - 计算社区营销ROI

### Tom Agent

- `track_cpm(impressions, clicks, cost)` - CPM 跟踪
- `generate_plan(brand, budget, city, industry)` - 方案生成
- `get_cities()` - 城市列表
- `get_stats()` - 统计数据
- `get_competitors()` - 竞品数据
- `get_summary()` - 汇总数据

### ROI Agent

- `calc_roi(frames, period_weeks, ...)` - ROI 计算（单场景）
- `calc_three_scenarios(N, cost, city, product)` - ROI 三场景计算（保守/中性/乐观）
- `get_categories()` - 品类参数
- `compare_competitors(category)` - 竞品对比
- `get_formula()` - 公式说明

### 竞品 Agent

- `get_competitors()` - 竞品列表
- `get_brands()` - 重点品牌
- `get_industries()` - 行业分类
- `get_intelligence(industry)` - 市场情报
- `get_intelligence_stats()` - 情报统计
- `search_intelligence(q)` - 情报搜索

## 🧪 测试

```bash
cd pdooh_client
pytest tests/ -v
```

## 📋 依赖

- `httpx` - 高性能 HTTP 客户端
- `pydantic` - 数据验证和类型标注

## 📝 许可证

MIT License

## 📧 联系

- 作者：Tom (Qi)
- 邮箱：tom@example.com
- GitHub：https://github.com/tomwugdgz/AIAdPlacer
