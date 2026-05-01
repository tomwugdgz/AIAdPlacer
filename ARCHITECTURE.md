# AIAdPlacer CPS 2.0 — 5C × 5V 架构设计

## 框架概述

AIAdPlacer 采用 **5C 社区框架** 与 **5V 数据特性** 相结合的架构设计理念，构建社区媒体数字化全链路解决方案。

### 5C 社区框架
| 维度 | 含义 | 核心问题 |
|------|------|----------|
| **Context** 场景上下文 | 理解用户当下所处环境 | 在哪里？什么时间？什么场景？ |
| **Community** 社区人群 | 理解目标受众特征 | 是谁？有什么特征？喜好什么？ |
| **Content** 内容创意 | 生成适配的创意素材 | 什么内容能打动这个人群？ |
| **Connection** 社区链接 | 打通线上线下触点 | 如何追踪完整用户路径？ |
| **Commerce** 商业转化 | 实现ROI最大化 | 如何量化效果？如何优化分成？ |

### 5V 数据特性
| 维度 | 含义 | 技术挑战 |
|------|------|----------|
| **Volume** 数据体量 | 处理百万级曝光/行为数据 | 存储、查询、聚合效率 |
| **Velocity** 数据速度 | 实时归因、分钟级优化 | 流式处理、缓存策略 |
| **Variety** 数据类型 | 多源异构数据融合 | LBS+APP+库存+画像 |
| **Value** 数据价值 | 从数据中提取商业价值 | ROI最大化、CPM优化 |
| **Veracity** 数据真实性 | 验证数据准确性和一致性 | 跨端匹配、去重验证 |

---

## 5C × 5V 矩阵

```
              Volume          Velocity         Variety           Value            Veracity
            ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  Context   │ 海量位置  │   │ 实时场景  │   │ LBS+天气  │   │ 精准场景  │   │ 位置验证  │
  场景上下文 │ 数据存储  │   │ 动态更新  │   │ +事件融合 │   │ 匹配度    │   │ 去重校验  │
            └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘

            ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
 Community  │ 百万用户  │   │ 动态聚类  │   │ 多平台    │   │ 高价值    │   │ 身份去重  │
 社区人群   │ 画像存储  │   │ 实时更新  │   │ 人群数据  │   │ 人群识别  │   │ 交叉验证  │
            └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘

            ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  Content   │ 千组创意  │   │ 实时DCO   │   │ 文本+图片 │   │ 高CTR     │   │ A/B测试   │
 内容创意   │ 素材库    │   │ 动态切换  │   │ +语音融合 │   │ 创意识别  │   │ 效果验证  │
            └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘

            ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
Connection  │ 全链路    │   │ 实时跨端  │   │ Cookie+   │   │ 高转化    │   │ 跨端身份  │
社区链接    │ 触点记录  │   │ 身份匹配  │   │ 设备指纹  │   │ 链路识别  │   │ 匹配验证  │
            └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘

            ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
 Commerce   │ 全量转化  │   │ 实时ROI   │   │ 线上+线下 │   │ ROI       │   │ 转化归因  │
 商业转化   │ 数据存储  │   │ 计算看板  │   │ 数据打通  │   │ 最大化    │   │ 效果验证  │
            └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## 系统架构映射

### 数据层 → 5V 实现

| 数据源 | Volume | Velocity | Variety | Value | Veracity |
|--------|--------|----------|---------|-------|----------|
| QADN点位 | 百万级位置记录 | 实时客流更新 | LBS+时段+天气 | 高价值点位筛选 | GPS精度验证 |
| 天工智投 | 全量库存数据 | 档期实时同步 | 多类型广告位 | 最优性价比计算 | 库存真实性 |
| 亲邻APP | 全量行为日志 | 实时行为采集 | 浏览+点击+购买 | 高转化路径识别 | 设备指纹校验 |
| 友盟画像 | 百万用户画像 | 动态标签更新 | 年龄+性别+兴趣 | 高价值人群定位 | 身份去重 |

### Agent层 → 5C 实现

| Agent | Context | Community | Content | Connection | Commerce |
|-------|---------|-----------|---------|------------|----------|
| 人群洞察 | LBS场景分析 | KMeans聚类 | 人群特征报告 | - | 高价值区域推荐 |
| 智能排期 | 时段优化 | 人群-点位匹配 | - | 跨平台协同 | 预算分配优化 |
| 动态创意 | 场景适配文案 | 人群定向创意 | AIGC+DCO | - | 高CTR预测 |
| 效果归因 | 地域效果分析 | 人群转化分析 | 创意效果对比 | 跨端匹配 | ROI实时看板 |

---

## 代码实现映射

### Context + Volume: `mock_data.py`
```python
# 场景上下文数据 → Volume海量存储
{
    "poi_id": "QADN_天河体育中心_01",    # 唯一标识
    "lat": 23.136, "lng": 113.326,       # 位置数据 (Volume)
    "foot_traffic_daily": 42500,          # 客流量 (Volume + Velocity)
    "peak_hours": [7, 8, 17, 18, 19],    # 时段特征 (Context)
    "dwell_time_avg_min": 8.5             # 停留时长 (Context)
}
```

### Community + Variety: `audience_insight.py`
```python
# 多源数据融合 → Variety
lbs_data = mock_data.get_qadn_location_data(city)        # LBS数据
umeng_data = mock_data.get_umeng_audience_data(city)     # 友盟画像
fused_data = self._fuse_data(lbs_data, umeng_data)       # 数据融合 (Variety)

# KMeans聚类 → Community
clusters = self._cluster_audience(fused_data)            # 人群分群 (Community)
```

### Content + Velocity: `dynamic_creative.py`
```python
# AIGC生成 → Content (Velocity:实时生成)
copies = await self._generate_copies_aigc(audience)

# DCO动态映射 → Content (Velocity:实时切换)
dco_map = self._create_dco_mapping(copies, schedule, audience)
```

### Connection + Veracity: `attribution.py`
```python
# 跨端匹配 → Connection (Veracity:身份验证)
merged_data = self._cross_device_match(online_data, offline_data)

# 多触点归因 → Connection (Veracity:路径验证)
multi_touch = self._multi_touch_attribution(merged_data)
```

### Commerce + Value: `attribution_engine.py`
```python
# ROI计算 → Commerce (Value:价值量化)
roi = (conversions * 100) / cost

# CPS动态分成 → Commerce (Value:价值分配)
if roi >= 300: commission = 0.30
elif roi >= 200: commission = 0.25
elif roi >= 100: commission = 0.18
else: commission = 0.10
```

---

## RAG知识库 → 5C×5V 赋能

```
                    用户查询
                       │
                       ▼
              ┌─────────────────┐
              │  顶层路由Agent   │ ← Context:理解查询意图
              └────────┬────────┘
                       │
           ┌───────────┼───────────┬───────────┐
           ▼           ▼           ▼           ▼
      ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
      │ 行业案例 │ │ 归因模型 │ │ 创意素材 │ │ 投放策略 │
      │ Community│ │Veracity │ │ Content │ │Commerce │
      └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
           │           │           │           │
           └───────────┴─────┬─────┴───────────┘
                             ▼
                    ┌─────────────────┐
                    │   重排序模型     │ ← Value:相关性排序
                    └────────┬────────┘
                             ▼
                       最终检索结果
```

---

## 关键指标 (5C×5V)

| 5C维度 | 核心指标 | 5V维度 | 技术实现 | 目标值 |
|--------|---------|--------|---------|--------|
| Context | 场景匹配度 | Velocity | 实时LBS更新 | < 1分钟 |
| Community | 聚类准确率 | Variety | 多源数据融合 | 68% |
| Content | 创意CTR | Value | DCO动态优化 | > 4% |
| Connection | 跨端匹配率 | Veracity | Cookie+指纹 | 68% |
| Commerce | ROI | Volume | 全量数据分析 | > 200% |

---

## 总结

AIAdPlacer CPS 2.0 通过 **5C × 5V** 框架实现了：

- **Context × Velocity**: 实时感知社区场景变化
- **Community × Variety**: 多源数据驱动精准人群画像
- **Content × Value**: AIGC+DCO实现创意价值最大化
- **Connection × Veracity**: 跨端身份验证确保数据真实
- **Commerce × Volume**: 海量数据驱动的ROI优化与动态分成

这一框架不仅指导了系统架构设计，也为后续功能迭代提供了清晰的演进方向。
