# 🚇 地铁 pDOOH 程序化投放 — 技术方案

> 基于**德高中国《地铁程序化数字户外白皮书》**权威方法论  
> 对齐标准：T/CCSA 738-2025 + T/CAAAD 006-2025

---

## 目录

1. [白皮书核心洞察](#1-白皮书核心洞察)
2. [系统架构升级方案](#2-系统架构升级方案)
3. [核心算法能力](#3-核心算法能力)
4. [数据库 schema 扩展](#4-数据库-schema-扩展)
5. [API 端点设计](#5-api-端点设计)
6. [前端 Dashboard 升级](#6-前端-dashboard-升级)
7. [实施路线图](#7-实施路线图)
8. [附录：白皮书案例索引](#8-附录白皮书案例索引)

---

## 1. 白皮书核心洞察

### 1.1 五大进化土壤

| # | 维度 | 对 AIAdPlacer 的启示 |
|---|------|----------------------|
| 1 | 户外媒体数字化转型 | 优先接入数字化媒体（智能屏 > 静态框架）|
| 2 | 数据丰富且可利用 | 接入 LBS / 移动设备定位 / 第三方 DMP |
| 3 | 户外投放数据需求 | 实现曝光量（Impression）可衡量、可追溯 |
| 4 | 全渠道协同趋势 | 设计 pDOOH ↔ 线上广告统一编排接口 |
| 5 | 线上广告瓶颈（注意力饱和）| 强化「线下互补」卖点，突出场景真实感 |

### 1.2 pDOOH 全球渗透数据（白皮书 Fig. p6）

| 市场 | pDOOH/DOOH 占比 | 启示 |
|------|------------------|------|
| 德国 | 32.4% | 成熟市场标杆 |
| 荷兰 | > 8.8%（全球均值）| 增长潜力大 |
| 比利时 | > 8.8%（全球均值）| 增长潜力大 |
| **中国** | < 8.8% | **高速增长窗口期** |

### 1.3 英国买家调研（白皮书 Fig. p7-p8）

选择 pDOOH 的**TOP 3 原因**：
1. **效能可衡量**（38%）→ 必须做好 Dashboard ROI 归因
2. **精准触达**（32%）→ 强化 TA 标签 + POI 定向
3. **创意灵活性**（20%）→ 支持 DCO 动态创意

### 1.4 八大增益价值（白皮书 Chap.5）

```
① 精准触达  → TA标签 + POI定向算法
② 效果可衡量 → MAM曝光测量 + 归因看板
③ 实时优化   → DCO引擎 + 外部数据联动
④ 跨渠道协同 → 人群包导出 + 再营销
⑤ 场景化创意 → 天气/时段/客流触发
⑥ 数据驱动   → CRM整合 + DMP标签
⑦ 全域营销   → 线上+线下统一编排
⑧ 标准化测量 → 符合T/CCSA 738-2025
```

---

## 2. 系统架构升级方案

### 2.1 当前架构（Chap.6 README）

```
┌─────────────────────────────────────────┐
│                 前端展示层                        │
│  demo.html（腾讯地图可视化）· bmn-frontend/     │
│  bus-demo.html（公交线路热力图）                │
└──────────────────┬─────────────────────────────┘
                     │ REST / WebSocket
┌─────────────────────────────────────────┐
│                FastAPI 后端层  (Port 5002)          │
│  /api/v2/pdooh/*  ·  /api/v2/agents/*           │
│  /api/v2/rag/*   ·  /api/v2/mcp/*  (A2A)      │
│  /api/v2/bus/*    ·  /api/v2/bus-bidding/*    │
└──────────────────┬─────────────────────────────┘
                     │
┌─────────────────────────────────────────┐
│                  AI 能力层                           │
│  LangGraph Agent 编排  ·  ChromaDB 向量检索       │
│  Ollama 本地 LLM (qwen3.5-9B)                  │
└──────────────────┬─────────────────────────────┘
                     │
┌─────────────────────────────────────────┐
│                  数据层                              │
│  PostgreSQL (pdooh + ai_adplacer)                │
│  Redis · ChromaDB                                 │
│  qinlin_local.db（社区点位，94,992条）              │
└─────────────────────────────────────────┘
```

### 2.2 升级后架构（新增 subway 模块）

```
┌─────────────────────────────────────────────────────────┐
│                       前端展示层                                      │
│  demo.html · bmn-frontend/ · bus-demo.html                    │
│  subway-demo.html ⭐ 【新增】地铁 pDOOH 可视化看板           │
└────────────────────────┬──────────────────────────────────────┘
                             │ REST / WebSocket
┌─────────────────────────────────────────────────────────┐
│                      FastAPI 后端层  (Port 5002)                    │
│  /api/v2/pdooh/*  ·  /api/v2/agents/*                     │
│  /api/v2/rag/*   ·  /api/v2/mcp/*  (A2A)                │
│  /api/v2/bus/*    ·  /api/v2/bus-bidding/*                │
│  /api/v2/subway/* ⭐ 【新增】地铁 pDOOH 模块                 │
│    ├─ /subway/screens          # 地铁屏点查询              │
│    ├─ /subway/exposure        # MAM曝光量计算              │
│    ├─ /subway/targeting      # TA/POI/外部数据定向        │
│    ├─ /subway/dco            # 动态创意触发                │
│    └─ /subway/retargeting   # 跨渠道再营销                │
└────────────────────────┬──────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────┐
│                        AI 能力层                                     │
│  LangGraph Agent 编排  ·  ChromaDB 向量检索                   │
│  Ollama 本地 LLM (qwen3.5-9B)                            │
│  MAM Integration ⭐ 【新增】德高MAM系统对接                   │
└────────────────────────┬──────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────┐
│                        数据层                                        │
│  PostgreSQL (pdooh + ai_adplacer)                          │
│  Redis · ChromaDB                                             │
│  qinlin_local.db（社区点位）                                    │
│  subway_exposure.db ⭐ 【新增】地铁客流量测算模型缓存           │
└─────────────────────────────────────────────────────────┘
```

### 2.3 MAM 系统集成方案

> **MAM（Media Audience Measurement）** — 德高集团 proprietary 地铁受众测量系统，获 CCSS + CAA 双权威背书。

#### 集成架构

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  MAM API    │────▶│  AIAdPlacer    │────▶│  投放计划              │
│  (德高提供) │     │  /subway/exposure│     │  Placement.impressions│
└──────────────┘     └──────────────────┘     └──────────────────────┘
```

#### 计算逻辑（白皮书 p11）

```
Impression = f(
    车站人数,
    客流动线,
    媒体尺寸,
    广告播放时长
)
```

#### 对接步骤

1. 与德高中国签署 MAM API 数据使用协议
2. 获取 API Key（`MAM_API_KEY`）
3. 实现 `app/services/mam_service.py`
4. 在 `Placement` 模型新增 `mam_impressions` 字段

---

## 3. 核心算法能力

### 3.1 曝光量测算模型（MAM 系统）

**文件**：`app/services/exposure_calculator.py`

```python
def calculate_impressions(
    station_id: str,
    screen_id: str,
    date: date,
    time_slot: str,  # "morning_peak" | "evening_peak" | "off_peak"
    ad_duration_sec: int = 15
) -> ImpressionResult:
    """
    基于MAM系统计算单屏单日曝光量
    对齐标准：T/CCSA 738-2025 §5.2
    """
    # 1. 获取车站客流数据
    passenger_flow = mam_client.get_station_flow(station_id, date)
    
    # 2. 计算驻留曝光乘数（dwell time factor）
    dwell_factor = calculate_dwell_factor(time_slot)
    
    # 3. 计算可视概率（screen visibility probability）
    visibility_prob = get_screen_visibility(screen_id)
    
    # 4. 计算播放频次
    play_freq = calculate_play_frequency(ad_duration_sec, time_slot)
    
    impressions = (
        passenger_flow
        * dwell_factor
        * visibility_prob
        * play_freq
    )
    
    return ImpressionResult(
        station_id=station_id,
        screen_id=screen_id,
        date=date,
        impressions=round(impressions),
        calculation_method="MAM_v2.0"
    )
```

### 3.2 TA 标签定向算法

**文件**：`app/services/ta_targeting.py`

```python
def match_ta_tags(
    screen_id: str,
    target_tags: List[str],  # e.g. ["18-34岁", "中产", "餐饮消费"]
    match_threshold: float = 0.6
) -> TAGMatchResult:
    """
    基于第三方DMP + 品牌CRM数据，匹配目标人群标签
    输出：匹配度评分 + 建议出价系数
    """
    # 1. 获取屏点周边人群画像
    screen_profile = get_screen_audience_profile(screen_id)
    
    # 2. 计算标签匹配度
    match_scores = []
    for tag in target_tags:
        score = calculate_tag_affinity(screen_profile, tag)
        match_scores.append((tag, score))
    
    # 3. 综合评分
    overall_score = weighted_average(match_scores)
    
    # 4. 生成出价建议
    bid_multiplier = 1.0 + (overall_score - match_threshold) * 0.5
    
    return TAGMatchResult(
        screen_id=screen_id,
        overall_match_score=round(overall_score, 2),
        tag_scores=dict(match_scores),
        suggested_bid_multiplier=round(bid_multiplier, 2)
    )
```

### 3.3 POI 场景定向算法

**文件**：`app/services/poi_targeting.py`

```python
def filter_by_poi(
    screens: List[Screen],
    poi_categories: List[str],  # e.g. [" retail", "stadium", "office"]
    radius_m: int = 500
) -> List[Screen]:
    """
    基于POI邻近关系筛选点位
    依赖：腾讯地图LBS API
    """
    matched_screens = []
    
    for screen in screens:
        # 1. 获取屏点POI列表
        nearby_pois = tencent_lbs.search_nearby(
            location=(screen.latitude, screen.longitude),
            radius=radius_m,
            categories=poi_categories
        )
        
        # 2. 计算POI匹配度
        if nearby_pois:
            screen.poi_match_count = len(nearby_pois)
            screen.poi_categories = [p.category for p in nearby_pois]
            matched_screens.append(screen)
    
    return sorted(matched_screens, 
                 key=lambda s: s.poi_match_count, reverse=True)
```

### 3.4 外部数据联动触发（DCO 引擎）

**文件**：`app/services/dco_engine.py`

```python
class DCOEngine:
    """
    动态创意优化引擎
    支持触发条件：气温 / 天气 / 时段 / 客流
    """
    
    def evaluate_triggers(self, screen_id: str, current_time: datetime) -> List[Creative]:
        triggers_fired = []
        
        # 1. 气温触发（参考脉动案例：≥33℃切换高温版）
        temp = get_current_temperature(screen_id)
        if temp >= 33.0:
            trigers_fired.append("high_temp_creative")
        elif 15 <= temp < 20:
            trigers_fired.append("mid_temp_creative")
        elif temp < 15:
            trigers_fired.append("low_temp_creative")
        
        # 2. 天气触发
        weather = get_current_weather(screen_id)
        if weather in ["rain", "snow"]:
            trigers_fired.append("weather_creative")
        
        # 3. 时段触发
        hour = current_time.hour
        if (7 <= hour <= 9) or (17 <= hour <= 19):
            trigers_fired.append("rush_hour_creative")
        
        # 4. 客流触发
        flow_rate = get_current_flow_rate(screen_id)
        if flow_rate > flow_rate_threshold * 1.5:
            trigers_fired.append("high_flow_creative")
        
        # 5. 匹配创意
        matched_creatives = self.match_creatives(triggers_fired)
        return matched_creatives
```

### 3.5 跨渠道再营销定向

**文件**：`app/services/retargeting.py`

```python
def build_retargeting_audience(
    campaign_id: UUID,
    lookback_days: int = 7
) -> AudiencePackage:
    """
    将pDOOH曝光过的受众整合为专属人群包
    用于：线上广告再营销
    """
    # 1. 获取曝光设备ID（脱敏后）
    exposed_devices = get_exposed_devices(
        campaign_id=campaign_id,
        lookback_days=lookback_days
    )
    
    # 2. 匹配到线上DMP
    matched_ids = []
    for device_id in exposed_devices:
        dmp_id = match_to_dmp(device_id)
        if dmp_id:
            matched_ids.append(dmp_id)
    
    # 3. 生成人群包
    audience_pkg = AudiencePackage(
        campaign_id=campaign_id,
        package_name=f"pDOOH_Exposed_{campaign_id}",
        device_count=len(matched_ids),
        dmp_ids=matched_ids,
        created_at=datetime.utcnow()
    )
    
    # 4. 推送到线上投放平台
    push_to_dsp(audience_pkg)
    
    return audience_pkg
```

---

## 4. 数据库 Schema 扩展

### 4.1 新增表：`subway_screens`

```sql
CREATE TABLE subway_screens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screen_id VARCHAR(64) UNIQUE NOT NULL,
    station_name VARCHAR(128) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    line_name VARCHAR(128),
    screen_type VARCHAR(32),  -- 'iScreen' | 'LED大屏'
    width_cm INT,
    height_cm INT,
    visibility_score FLOAT,  -- 0.0 ~ 1.0（MAM系统提供）
    dwell_time_sec INT,  -- 平均驻留时长
    daily_impressions INT,  -- MAM计算值
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subway_city ON subway_screens(city);
CREATE INDEX idx_subway_station ON subway_screens(station_id);
```

### 4.2 新增表：`creative_rules`（DCO 规则）

```sql
CREATE TABLE creative_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    trigger_type VARCHAR(32) NOT NULL,  -- 'temperature' | 'weather' | 'time_slot' | 'flow_rate'
    trigger_condition JSONB NOT NULL,  -- {"op": ">=", "value": 33}
    creative_id UUID REFERENCES creatives(id),
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rules_campaign ON creative_rules(campaign_id);
```

### 4.3 `placements` 表扩展

```sql
ALTER TABLE placements ADD COLUMN mam_impressions INT;  -- MAM系统计算值
ALTER TABLE placements ADD COLUMN ta_match_score FLOAT;  -- TA标签匹配度
ALTER TABLE placements ADD COLUMN poi_categories TEXT[];  -- POI场景标签
```

---

## 5. API 端点设计

### 5.1 地铁屏点查询

```
GET /api/v2/subway/screens
```

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `city` | string | 否 | 城市筛选 |
| `line_name` | string | 否 | 线路筛选 |
| `station_name` | string | 否 | 站点模糊搜索 |
| `min_impressions` | int | 否 | 最小曝光量 |
| `poi_category` | string | 否 | POI类别（零售/餐饮/写字楼）|
| `ta_tags` | string | 否 | TA标签（逗号分隔）|

**响应示例**：

```json
{
  "screens": [
    {
      "screen_id": "SH-Metro-Line2-001",
      "station_name": "人民广场",
      "city": "上海",
      "line_name": "2号线",
      "screen_type": "LED大屏",
      "daily_impressions": 125000,
      "ta_match_score": 0.82,
      "poi_categories": ["零售", "餐饮", "写字楼"]
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20
}
```

### 5.2 MAM 曝光量计算

```
POST /api/v2/subway/exposure/calculate
```

**请求体**：

```json
{
  "placements": [
    {
      "screen_id": "SH-Metro-Line2-001",
      "date": "2026-07-01",
      "time_slots": ["morning_peak", "evening_peak"],
      "ad_duration_sec": 15
    }
  ]
}
```

**响应体**：

```json
{
  "results": [
    {
      "screen_id": "SH-Metro-Line2-001",
      "date": "2026-07-01",
      "impressions": 125000,
      "calculation_method": "MAM_v2.0",
      "confidence_level": "A级" 
    }
  ]
}
```

### 5.3 DCO 规则配置

```
POST /api/v2/subway/dco/rules
```

**请求体**：

```json
{
  "campaign_id": "uuid",
  "rules": [
    {
      "trigger_type": "temperature",
      "trigger_condition": {"op": ">=", "value": 33},
      "creative_id": "uuid-hot-version",
      "priority": 10
    },
    {
      "trigger_type": "temperature",
      "trigger_condition": {"op": "<", "value": 15},
      "creative_id": "uuid-cold-version",
      "priority": 10
    }
  ]
}
```

### 5.4 跨渠道再营销人群包导出

```
POST /api/v2/subway/retargeting/export
```

**请求体**：

```json
{
  "campaign_id": "uuid",
  "lookback_days": 7,
  "push_to_dsp": true,
  "dsp_platforms": ["tencent_ads", "byedance_ads"]
}
```

**响应体**：

```json
{
  "audience_package_id": "uuid",
  "device_count": 125000,
  "push_status": {
    "tencent_ads": "success",
    "byedance_ads": "success"
  }
}
```

---

## 6. 前端 Dashboard 升级

### 6.1 新增页面：`subway-demo.html`

**功能模块**：

```
┌──────────────────────────────────────────────┐
│  地铁 pDOOH 投放看板                          │
├──────────────────────────────────────────────┤
│  [模块1] 线路总览                             │
│    - 覆盖城市数 / 线路数 / 屏点数            │
│    - 总曝光量（Impressions）                  │
│    - 平均 CPRP（每收视点成本）               │
├──────────────────────────────────────────────┤
│  [模块2] 线路热力地图（腾讯地图）           │
│    - 按线路渲染屏点                         │
│    - 颜色深浅 = 曝光量大小                  │
│    - 点击查看屏点详情                       │
├──────────────────────────────────────────────┤
│  [模块3] TA 标签定向模拟器                  │
│    - 输入目标标签 → 查看匹配屏点             │
│    - 匹配度评分可视化                       │
├──────────────────────────────────────────────┤
│  [模块4] POI 场景定向模拟器                 │
│    - 选择POI类别 → 查看邻近屏点             │
│    - 距离半径滑块                           │
├──────────────────────────────────────────────┤
│  [模块5] DCO 规则配置器                    │
│    - 可视化配置触发条件                      │
│    - 实时预览创意切换效果                   │
├──────────────────────────────────────────────┤
│  [模块6] ROI 趋势图（复用现有Echarts）     │
│    - 按线路分组                            │
│    - 对比不同线路ROI                       │
└──────────────────────────────────────────────┘
```

### 6.2 Echarts 图表配置（扩展）

在现有 `updateROITrendChart()` 基础上，新增：

```javascript
// 按线路分组的ROI对比
function renderSubwayROITrendChart(data) {
    // ... 现有逻辑 ...
    
    // 新增：按线路分组
    const lineSeries = {};
    data.forEach(d => {
        const lineName = d.line_name;
        if (!lineSeries[lineName]) {
            lineSeries[lineName] = { name: lineName, type: 'line', data: [] };
        }
        lineSeries[lineName].data.push([d.date, d.roi]);
    });
    
    // 添加到 option.series
    option.series = Object.values(lineSeries);
}
```

---

## 7. 实施路线图

### Phase 1：基础设施（Week 1-2）

- [ ] 创建 `subway_screens` 表 + 数据导入脚本
- [ ] 实现 `mam_service.py`（MAM API 对接）
- [ ] 扩展 `placements` 表（新增 `mam_impressions` 等字段）
- [ ] 编写单元测试（目标覆盖率 > 80%）

### Phase 2：定向算法（Week 3-4）

- [ ] 实现 `ta_targeting.py`（TA标签定向）
- [ ] 实现 `poi_targeting.py`（POI场景定向）
- [ ] 对接腾讯地图LBS API
- [ ] 新增 API 端点：`/api/v2/subway/screens`

### Phase 3：DCO 引擎（Week 5-6）

- [ ] 创建 `creative_rules` 表
- [ ] 实现 `dco_engine.py`
- [ ] 对接天气 API（OpenWeatherMap / 和风天气）
- [ ] 新增 API 端点：`/api/v2/subway/dco/*`

### Phase 4：再营销（Week 7-8）

- [ ] 实现 `retargeting.py`
- [ ] 对接主流DSP（腾讯广告 / 字节巨量引擎）
- [ ] 新增 API 端点：`/api/v2/subway/retargeting/*`

### Phase 5：前端集成（Week 9-10）

- [ ] 创建 `subway-demo.html`
- [ ] 集成腾讯地图 GL JS（线路热力图）
- [ ] 实现 TA/POI 定向模拟器
- [ ] 实现 DCO 规则配置器

### Phase 6：测试 & 上线（Week 11-12）

- [ ] 端到端测试
- [ ] 性能压测（目标：500 QPS）
- [ ] 编写用户手册
- [ ] 部署到生产环境

---

## 8. 附录：白皮书案例索引

### 案例 1：阿德莱德大学（跨城精准获客）

| 维度 | 内容 |
|------|------|
| 行业 | 公共事业（教育） |
| 投放范围 | 北京、上海、香港 |
| 核心策略 | 意图定向 + 全域协同 |
| 技术亮点 | 航班信息 + 校园周边LBS定位 + 高峰时段定向 |
| 启示 | 支持「多城市联合投放」编排 |

### 案例 2：道达尔（全球统一布局）

| 维度 | 内容 |
|------|------|
| 行业 | 能源 |
| 投放范围 | 中国（上海、北京）+ 美、英、印等12国 |
| 核心策略 | 程序化同步技术 |
| 技术亮点 | 跨时区内容协同 + 数据统一汇总 |
| 启示 | 支持「全球多时区编排」 |

### 案例 3：探探糖（平台化降本）

| 维度 | 内容 |
|------|------|
| 行业 | 在线平台（本地生活） |
| 投放范围 | 上海地铁、北京地铁 |
| 核心策略 | 集中采购 + 智能调度 |
| 技术亮点 | 素材轮播 + 应需分发 + 流动式管理 |
| 启示 | 支持「多商户联合投放」模式 |

### 案例 4：嘉士伯（多品牌差异化管理）

| 维度 | 内容 |
|------|------|
| 行业 | 啤酒 |
| 投放范围 | 上海地铁（乌苏）、北京地铁（1664）、重庆地铁（重庆啤酒） |
| 核心策略 | 分品牌独立定向 + 统一管理后台 |
| 技术亮点 | 高峰时段集中投放 + TA标签差异化 |
| 启示 | 支持「多品牌矩阵管理」 |

### 案例 5：脉动（场景化创意）

| 维度 | 内容 |
|------|------|
| 行业 | 食品饮料 |
| 投放范围 | 上海地铁 |
| 核心策略 | 气温触发 DCO |
| 技术亮点 | 气温≥33℃ → 切换高温版素材 |
| 启示 | DCO引擎「气温触发」优先级：P0 |

### 案例 6：优衣库（温度触发）

| 维度 | 内容 |
|------|------|
| 行业 | 服饰 |
| 投放范围 | 上海地铁（优衣库旗舰店楼下站） |
| 核心策略 | 温度触发 + POI定向 |
| 技术亮点 | <15℃播轻薄羽绒服；15~20℃播保暖内衣；>20℃不展示 |
| 启示 | DCO引擎「温度触发」完整实现参考 |

### 案例 7：亨氏（策略优化）

| 维度 | 内容 |
|------|------|
| 行业 | 食品杂货 |
| 投放范围 | 上海地铁、北京地铁 |
| 核心策略 | 分组轮换投放 |
| 技术亮点 | 15个核心站点分为4~5组，每日一组依次轮换 |
| 启示 | 支持「频控优化」算法（避免重复曝光） |

---

## 变更记录

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2026-07-01 | v1.0 | 初始版本，基于德高白皮书 | Qi（主理人）|

---

**参考文档**：
- 德高中国《地铁程序化数字户外白皮书》（2025版）
- T/CCSA 738-2025《程序化户外广告投放曝光测量技术要求》
- T/CAAAD 006-2025《程序化户外广告投放曝光测量技术要求》
- AIAdPlacer README.md（v2.0.1）
