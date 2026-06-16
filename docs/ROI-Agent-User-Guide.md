# ROI Agent 调用指南

**版本**：v2.1  
**服务地址**：`http://47.253.159.62:5004`  
**更新时间**：2026-06-16

---

## 目录

1. [服务状态](#1-服务状态)
2. [媒体价格参考](#2-媒体价格参考)
3. [品类参数说明](#3-品类参数说明)
4. [API 接口详解](#4-api-接口详解)
5. [计算公式说明](#5-计算公式说明)
6. [测试结果示例](#6-测试结果示例)
7. [投放方案对比](#7-投放方案对比)
8. [Python 调用示例](#8-python-调用示例)
9. [快速查询命令](#9-快速查询命令)
10. [商务应用建议](#10-商务应用建议)

---

## 1. 服务状态

在调用前建议先检查服务健康状态：

```bash
curl http://47.253.159.62:5004/health
```

**响应示例**：

```json
{
  "status": "ok",
  "version": "v2.0",
  "categories": [
    "日化用品", "食品饮料", "母婴用品", "美妆护肤",
    "家电数码", "汽车用品", "医药保健", "餐饮连锁", "通用"
  ]
}
```

---

## 2. 媒体价格参考

以下是社区媒体投放的两种主流合作模式的价格参考：

| 媒体类型 | 刊例价（公开价） | 置换价（资源置换） | 说明 |
|----------|-------------------|-------------------|------|
| 单元门智能框架 | ¥1,180 / 周·框 | ¥65 / 周·框 | 社区单元门入口处 |
| 广告门（道闸） | ¥2,640 / 2周 | ¥500 / 周 | 社区车辆出入口 |

**价格说明**：

- **刊例价**：公开报价，适合现金采购
- **置换价**：以物易物的资源置换价格，ROI 更优
- **年框价**：年度框架协议价，通常低于刊例价但高于置换价

---

## 3. 品类参数说明

不同品类的消费者记忆率、客单价、复购周期差异较大，直接影响 ROI 测算结果。

| 品类 | 记忆率区间 | 客单价区间 | 复购周期 | 消费特点 |
|------|------------|------------|----------|----------|
| 日化用品 | 15%–22% | ¥15–¥40 | 4周 | 高频复购，刚需 |
| 食品饮料 | 12%–20% | ¥10–¥35 | 2周 | 超高频复购 |
| 母婴用品 | 18%–28% | ¥50–¥200 | 8周 | 高客单价，高粘性 |
| 美妆护肤 | 20%–32% | ¥80–¥300 | 12周 | 高毛利，品牌忠诚度高 |
| 家电数码 | 8%–18% | ¥200–¥1000 | 52周 | 低频高价，决策周期长 |
| 汽车用品 | 6%–15% | ¥300–¥1200 | 104周 | 极低频，高客单价 |
| 医药保健 | 15%–26% | ¥30–¥120 | 6周 | 刚需，复购稳定 |
| 餐饮连锁 | 18%–35% | ¥25–¥100 | 3周 | 超高频，本地化强 |
| 通用（默认） | 15%–22% | ¥20–¥100 | 4周 | 适用于未分类品类 |

**参数说明**：

- **记忆率**：看到广告后能有效记住品牌的用户比例
- **客单价**：该品类消费者的平均单次消费金额
- **复购周期**：消费者重复购买的平均周期（周）

---

## 4. API 接口详解

### 4.1 POST /api/roi — ROI 计算（核心接口）

计算指定品类、投放规模的 ROI 测算结果，返回三场景（悲观/中性/乐观）。

**请求示例**：

```bash
curl -X POST http://47.253.159.62:5004/api/roi \
  -H "Content-Type: application/json" \
  -d '{"category": "日化用品", "frames": 5000, "period_weeks": 2}'
```

**请求参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `category` | string | `"通用"` | 品类名称（须与第3章品类参数匹配） |
| `frames` | integer | `5000` | 投放框数（单元门框架数量） |
| `period_weeks` | integer | `2` | 投放周期（周） |
| `media_type` | string | `"unit_door"` | 媒体类型：`unit_door` / `daocha` |
| `price_type` | string | `"exchange"` | 价格类型：`list`（刊例价）/ `exchange`（置换价）/ `annual`（年框价） |
| `custom_investment` | float | `null` | 自定义投入金额（元），设置后忽略 `price_type` 自动计算 |

**响应示例**：

```json
{
  "scenarios": {
    "pessimistic": {
      "memory": 64004,
      "orders": 2560,
      "first_purchase": 38400,
      "ltv_8weeks": 138240,
      "roi_percent": 21
    },
    "neutral": {
      "memory": 76805,
      "orders": 3072,
      "first_purchase": 76800,
      "ltv_8weeks": 399360,
      "roi_percent": 61
    },
    "optimistic": {
      "memory": 93873,
      "orders": 3754,
      "first_purchase": 150160,
      "ltv_8weeks": 1126200,
      "roi_percent": 173
    }
  },
  "summary": {
    "uv": 426700,
    "investment": 650000,
    "price_type": "exchange",
    "frames": 5000,
    "period_weeks": 2
  }
}
```

**响应字段说明**：

| 字段 | 单位 | 说明 |
|------|------|------|
| `uv` | 人 | 预估触达独立用户数 |
| `investment` | 元 | 总投入金额 |
| `memory` | 人 | 品牌记忆人数（UV × 记忆率） |
| `orders` | 单 | 转化订单数（记忆人数 × 转化率） |
| `first_purchase` | 元 | 首期销售额 |
| `ltv_8weeks` | 元 | 8周客户生命周期价值 |
| `roi_percent` | % | ROI = LTV / 投入 × 100% |

---

### 4.2 GET /api/media — 媒体价格查询

```bash
curl http://47.253.159.62:5004/api/media
```

返回完整的媒体类型、刊例价、置换价对照表。

---

### 4.3 GET /api/categories — 品类参数查询

```bash
curl http://47.253.159.62:5004/api/categories
```

返回所有品类的记忆率、客单价、复购周期等参数。

---

### 4.4 GET /api/compare — 跨品类 ROI 对比

```bash
curl http://47.253.159.62:5004/api/compare
```

返回各品类在标准投放条件（5000框×2周×置换价）下的 ROI 对比数据。

---

### 4.5 GET /api/formula — 计算公式说明

```bash
curl http://47.253.159.62:5004/api/formula
```

返回 ROI 计算过程中使用的所有公式及参数说明。

---

### 4.6 POST /api/compare-scenarios — 三方案对比

并排对比现金试投、置换合作、年框合作三种采购方案的 ROI 差异。

**请求示例**：

```bash
curl -X POST http://47.253.159.62:5004/api/compare-scenarios \
  -H "Content-Type: application/json" \
  -d '{"category": "日化用品", "frames": 5000, "period_weeks": 2}'
```

**响应示例**：

```json
{
  "category": "日化用品",
  "frames": 5000,
  "period_weeks": 2,
  "plans": {
    "cash_trial": {
      "name": "现金试投（刊例价）",
      "price_per_week": 1180,
      "total_investment": 11800000,
      "roi_percent": 3
    },
    "exchange": {
      "name": "置换合作（资源置换）",
      "price_per_week": 65,
      "total_investment": 650000,
      "roi_percent": 61
    },
    "annual": {
      "name": "年框合作（框架协议）",
      "price_per_week": 50,
      "total_investment": 13000000,
      "roi_percent": 3
    }
  },
  "recommendation": "exchange"
}
```

---

## 5. 计算公式说明

ROI Agent 使用以下公式计算投放效果：

### 5.1 UV（独立触达人数）

```
UV = 框数
   × 100 户/栋（社区平均户数）
   × 2.51 人/户（社区平均家庭人口）
   × 0.85 接触率（经过框架的人群比例）
   × 投放周期 × 2 次/天（每天上下各1次）
   ÷ 7 天/周（换算为周）
   × 0.7 去重系数（同一社区多次曝光去重）
```

### 5.2 品牌记忆人数

```
记忆人数 = UV × 品类记忆率（15%–35%）
```

### 5.3 转化订单数

```
订单数 = 记忆人数 ×（扫码率 1% + 到店率 3%）
```

### 5.4 首期销售额

```
首期销售 = 订单数 × 品类客单价（¥10–¥1000）
```

### 5.5 8周LTV（客户生命周期价值）

```
LTV₈ = 首期销售
    ×（8周 ÷ 复购周期）
    × 复购系数（1.2，假设复购客单价更高）
    × 口碑系数（1.5，假设口碑传播带来额外销售）
```

### 5.6 ROI

```
ROI = LTV₈ ÷ 总投入 × 100%
```

---

## 6. 测试结果示例

以下为 5000 框 × 2 周投放、置换价（¥65/框·周）的测算结果。

### 6.1 日化用品

| 场景 | 记忆人数 | 转化订单 | 首期销售 | 8周LTV | ROI |
|------|----------|----------|----------|---------|-----|
| 悲观 | 64,004 | 2,560 | ¥38,400 | ¥138,240 | 21% |
| 中性 | 76,805 | 3,072 | ¥76,800 | ¥399,360 | 61% |
| 乐观 | 93,873 | 3,754 | ¥150,160 | ¥1,126,200 | 173% |

### 6.2 餐饮连锁

| 场景 | 记忆人数 | 转化订单 | 首期销售 | 8周LTV | ROI |
|------|----------|----------|----------|---------|-----|
| 悲观 | 76,805 | 5,376 | ¥134,400 | ¥806,400 | 124% |
| 中性 | 106,674 | 7,467 | ¥373,350 | ¥3,982,400 | 613% |
| 乐观 | 149,344 | 10,454 | ¥1,045,400 | ¥20,908,000 | 3217% |

### 6.3 家电数码

| 场景 | 记忆人数 | 转化订单 | 首期销售 | 8周LTV | ROI |
|------|----------|----------|----------|---------|-----|
| 悲观 | 34,135 | 512 | ¥102,400 | ¥22,528 | 3% |
| 中性 | 51,203 | 768 | ¥384,000 | ¥113,428 | 17% |
| 乐观 | 76,805 | 1,152 | ¥1,152,000 | ¥531,692 | 82% |

---

## 7. 投放方案对比

同一投放规模下，不同采购方案的 ROI 对比（以日化用品 5000 框 × 2 周为例）：

| 方案 | 单框周价 | 总投入（5000框×2周） | 日化ROI | 餐饮ROI | 推荐度 |
|------|---------|---------------------|---------|---------|--------|
| A：现金试投（刊例价） | ¥1,180 | ¥11,800,000 | 3% | 34% | ⭐ |
| B：置换合作（资源置换） | ¥65 | ¥650,000 | **61%** | **613%** | ⭐⭐⭐ |
| C：年框合作（框架协议） | ¥50 | ¥13,000,000 | 3% | 31% | ⭐ |

**结论**：置换合作方案的 ROI 最高，建议优先向广告主推荐。

---

## 8. Python 调用示例

### 8.1 安装依赖

```bash
pip install requests
```

### 8.2 完整调用代码

```python
import requests
from typing import Dict, Any, Optional

ROI_BASE = "http://47.253.159.62:5004"

def calc_roi(
    category: str,
    frames: int,
    period_weeks: int,
    price_type: str = "exchange"
) -> Optional[Dict[str, Any]]:
    """
    ROI 测算
    """
    resp = requests.post(
        f"{ROI_BASE}/api/roi",
        json={
            "category": category,
            "frames": frames,
            "period_weeks": period_weeks,
            "price_type": price_type
        },
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

def compare_plans(
    category: str,
    frames: int,
    period_weeks: int
) -> Optional[Dict[str, Any]]:
    """
    三方案对比：现金试投 vs 置换合作 vs 年框合作
    """
    resp = requests.post(
        f"{ROI_BASE}/api/compare-scenarios",
        json={
            "category": category,
            "frames": frames,
            "period_weeks": period_weeks
        },
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()

# === 使用示例 ===

# 测算日化用品 ROI
result = calc_roi("日化用品", frames=5000, period_weeks=2)
if result:
    neutral = result["scenarios"]["neutral"]
    print(f"中性场景：记忆 {neutral['memory']} 人，ROI {neutral['roi_percent']}%")

# 三方案对比
result = compare_plans("餐饮连锁", frames=5000, period_weeks=2)
if result:
    recommended = result["recommendation"]
    for plan_id, plan_data in result["plans"].items():
        tag = " ← 推荐" if plan_id == recommended else ""
        print(f"{plan_data['name']}：ROI {plan_data['roi_percent']}%{tag}")
```

---

## 9. 快速查询命令

```bash
# ROI 测算（日化用品，5000框，2周）
curl -X POST http://47.253.159.62:5004/api/roi \
  -H "Content-Type: application/json" \
  -d '{"category": "日化用品", "frames": 5000, "period_weeks": 2}'

# 三方案对比
curl -X POST http://47.253.159.62:5004/api/compare-scenarios \
  -H "Content-Type: application/json" \
  -d '{"category": "餐饮连锁", "frames": 5000, "period_weeks": 2}'

# 跨品类 ROI 对比
curl http://47.253.159.62:5004/api/compare

# 媒体价格查询
curl http://47.253.159.62:5004/api/media

# 品类参数查询
curl http://47.253.159.62:5004/api/categories

# 计算公式说明
curl http://47.253.159.62:5004/api/formula
```

---

## 10. 商务应用建议

### 10.1 ROI 展示话术参考

> 「根据我们的数据模型测算，投放 5000 框社区单元门，持续 2 周：
> 
> - 悲观场景 ROI 21%（保本线以上）
> - 中性场景 ROI 61%（稳健可期）
> - 乐观场景 ROI 173%（品牌爆发增长）
> 
> 社区媒体的 LTV ROI 普遍在 150%–2500% 区间，与线上效果广告同属第一梯队，且具备更强的品牌记忆和本地化优势。」

### 10.2 品类推荐优先级

根据中性场景 ROI 排序，推荐优先级如下：

| 优先级 | 品类 | 推荐理由 | 中性ROI |
|--------|------|----------|---------|
| ⭐⭐⭐ | 餐饮连锁 | 超高频复购（3周）、本地化强、转化路径短 | 613% |
| ⭐⭐ | 食品饮料 | 高频复购（2周）、年轻群体覆盖好 | 124% |
| ⭐⭐ | 日化用品 | 稳定复购（4周）、刚需、记忆率高 | 61% |
| ⭐ | 美妆护肤 | 高客单价、高毛利、适合品牌种草 | 待测算 |
| ⭐ | 母婴用品 | 高净值人群、口碑传播强 | 待测算 |
| ⭐ | 家电数码 | 高客单价、适合大促节点投放 | 17% |

### 10.3 投放策略建议

1. **首试投放**：建议 3000–5000 框，2–4 周，置换价，控制试错成本
2. **规模化投放**：ROI 验证后扩至 10000+ 框，配合节假日营销节点
3. **组合投放**：单元门 + 智能屏组合，覆盖社区入口和电梯等待场景
4. **数据回收**：投放后回收 OTC 数据，用于下一轮 ROI 校准

---

## 11. 关联服务

ROI Agent 与 MCP 工具服务可配合使用：

1. 通过 **MCP 工具**（`pdooh_query_city_resources`）查询目标城市可投放资源量
2. 通过 **ROI Agent**（`/api/roi`）测算该资源量的 ROI
3. 通过 **MCP 工具**（`pdooh_create_campaign`）创建投放计划

---

## 12. 联系方式

| 事项 | 信息 |
|------|------|
| 商务咨询 | Tom `17665188615` |
| 媒体方 | 亲邻传媒 |
| 技术支持 | 通过商务联系人转接 |

---

*最后更新：2026-06-16*
