# 程序化户外广告曝光测量 — 术语表 & 行业标准应用指南

> **标准来源**：T/CCSA 738—2025 / T/CAAAD 040—2025  
> **发布机构**：中国广告协会 + 中国通信标准化协会  
> **发布日期**：2025-12-01 | **实施日期**：2026-03-01  
> **起草单位**：德高广告、中国广告协会、中国信息通信研究院、明略科技  
> **AIAdPlacer 适配版本**：v2.1（基于行业标准优化）

---

## 一、核心术语表（行业标准定义 → AIAdPlacer 映射）

### 1. 基础角色术语

| 术语 | 英文 | 标准定义 | AIAdPlacer 实现 |
|------|------|----------|-----------------|
| **广告主** | advertiser | 为推销商品、提供服务或推广概念而发布广告信息的市场主体 | `bus_campaigns.advertiser_id`、`campaigns.advertiser_id` |
| **媒体** | media | 发布、展示广告的载体 | `media_resources` 表（智能屏）、`bus_routes`（公交车身） |
| **受众** | audience | 广告主投放广告曝光并产生影响的人群 | `oneid_registry`（OneID 模型）、`person_anchor`（5V 人口属性） |
| **户外广告媒体运营商** | outdoor advertising media operator | 拥有或代理户外广告媒体资源，负责广告位租赁、发布、维护及安全管理 | 平台运营角色（批量导入线路、管理媒体资源） |

### 2. 曝光测量核心术语

| 术语 | 英文 | 标准定义 | AIAdPlacer 当前实现 | 标准对齐度 |
|------|------|----------|---------------------|------------|
| **程序化户外广告** | programmatic DOOH | 利用计算机算法和数据技术，实现自动化购买、优化和交付广告的方法 | ✅ FastAPI + LangGraph Agent 编排 + 竞价引擎 | 🟢 完全对齐 |
| **户外受众曝光测量** | out-of-home audience impression measurement | 对户外广告受众在广告投放区域内的曝光行为进行系统化测量与评估 | ⚠️ 有归因引擎但缺标准化计算流程 | 🟡 需补充 |
| **接触频次** | frequency | 平均每个个体看到 DOOH&OOH 广告的次数（≥1 次）。公式 = 广告有效展示次数 / 独立受众数量 | ⚠️ 有 estimated_impressions 但无 frequency 字段 | 🟡 需补充 |
| **户外广告曝光量** | impression | 户外广告在某一段时间内展示或出现的总次数，不考虑观众是否实际看到 | ✅ `bus_attribution.total_impressions` | 🟢 完全对齐 |
| **有效曝光量** | effective impression | 户外广告在目标受众中实际被注意到并且具有影响力的曝光次数 | ❌ 未实现（需引入曝光乘数） | 🔴 需新增 |
| **有效曝光时长** | effective impression duration | 户外广告在用户视野中持续存在并被有效注意到的时间长度 | ❌ 未实现 | 🔴 需新增 |
| **曝光乘数** | impression multiplier | 每播放一次广告片所产生的曝光量。公式 = (flow_Traffic × IMP) / ad_slots | ❌ 未实现（标准公式 6） | 🔴 需新增 |
| **流动曝光量** | dynamic impression | 广告在动态环境中（公交车、地铁等）被看到的次数 | ✅ bus-pDOOH 已覆盖动态媒体 | 🟢 部分对齐 |
| **驻留曝光量** | dwell impression | 广告在固定地点或静态场所展示的次数（观众停留时间长） | ❌ 未区分流动/驻留 | 🔴 需补充 |
| **曝光概率** | OTC (Opportunity to See) | 广告被目标受众看到的机会 | ✅ 有 OTC 概念但公式不同 | 🟡 需对齐标准公式 |

### 3. 算法 & 数据术语

| 术语 | 英文 | 标准定义 | AIAdPlacer 实现 |
|------|------|----------|-----------------|
| **迪杰斯特拉算法** | Dijkstra's algorithm | 寻找图中某一节点到其他所有节点的最短路径，解决人群流动路径优化 | ❌ 未实现（标准推荐用于地铁/机场场域） |
| **DMP** | Data Management Platform | 数据管理平台 | ⚠️ 有 `person_dmp_tags` 但非独立 DMP |
| **DSP** | Demand Side Platform | 需求方平台 | ✅ bus-pDOOH 竞价引擎本质是 DSP |
| **LBS** | Location Based Service | 基于移动位置服务 | ✅ 腾讯地图 API + 高德地图交叉比对 |
| **SOT** | Share of Time | 时间占比（特定广告在总播放时间中的比例） | ❌ 未实现（标准曝光计算关键参数） |

---

## 二、标准曝光量计算方法（公式对照）

### 标准公式 vs AIAdPlacer 当前实现

| 参数 | 标准公式 | AIAdPlacer 当前实现 | 对齐方案 |
|------|----------|---------------------|----------|
| **流动曝光概率** | `flow_OTC = (max(T_exposure, T_ad) - T_ad) / max(T_exposure, 2)` 公式(2) | ❌ 无 | 新增 `exposure_duration` 和 `ad_duration` 字段 |
| **流动曝光量** | `flow_IMP = flow_OTC × SOT × Traffic` 公式(1) | `impressions = vehicles × daily_traffic × hotspot_traffic × days` | 需增加 SOT 和 flow_OTC |
| **驻留曝光概率** | `dwell_OTC = T_exposure / 300`（5分钟=300秒）公式(4) | ❌ 无 | 新增驻留场景识别 |
| **驻留曝光量** | `dwell_IMP = dwell_OTC × Traffic` 公式(3) | ❌ 无 | 新增驻留曝光计算 |
| **总曝光量** | `IMP = flow_IMP + dwell_IMP` 公式(5) | 仅流动曝光 | 需合并流动+驻留 |
| **曝光乘数** | `ImpressionMultiplier = (flow_Traffic × IMP) / ad_slots` 公式(6) | ❌ 无 | 新增曝光乘数计算 |
| **接触频次** | `Frequency = 广告有效展示次数 / 独立受众数量` | ❌ 无 | 新增 frequency 计算 |

### 关键差异分析

1. **标准把曝光分为"流动"和"驻留"两类**，AIAdPlacer 目前只有统一的曝光计算
2. **标准引入 SOT（时间占比）**，AIAdPlacer 未考虑广告轮播时间分配
3. **标准有曝光乘数概念**，衡量每次播放产生的实际曝光效果
4. **标准用迪杰斯特拉算法优化人群流动路径**，AIAdPlacer 用热力评分但无路径优化

---

## 三、数据基础要求对照

### 标准 6.1 典型数据源 vs AIAdPlacer

| 标准数据源 | 要求 | AIAdPlacer 现状 | 适配方案 |
|-----------|------|-----------------|----------|
| **场域运营方数据** | 利用轧机数据记录进出时间、地点 | ❌ 无（门禁数据有但非标准轧机） | 利用现有 `spatial_trajectory`（门禁动作 V4） |
| **电信运营商数据** | 手机 GPS/Wi-Fi/蓝牙信号追踪移动轨迹 | ⚠️ 有腾讯地图 API 但非运营商直连 | 接入运营商 LBS 数据或模拟 |
| **地理信息数据** | 地图 POI、路网等 | ✅ 腾讯地图 + 高德地图交叉比对 | 🟢 已覆盖 |
| **移动应用数据** | App 使用行为 | ⚠️ OneID 跨 App 打通（规划中） | 持续推进 OneID |
| **图像识别数据** | 摄像头/人脸识别 | ❌ 无 | 合规前提下可引入（需 Hash 化） |
| **天气数据** | 天气影响客流 | ❌ 无 | V1.1 新增 |
| **交通流量数据** | 道路拥堵/公交到站 | ⚠️ bus-pDOOH 有部分 | 扩展交通 API |

### 标准 6.2 数据工作流程 vs AIAdPlacer

| 流程环节 | 标准要求 | AIAdPlacer 现状 |
|----------|----------|-----------------|
| **数据收集** | 自动化收集地理位置、移动定位、环境数据、广告内容、设备标识符；实时或定期更新 | ⚠️ 部分自动化（腾讯地图 API + Excel 导入），缺实时更新 |
| **数据处理** | 数据清洗、预处理、匹配、关联分析 | ⚠️ 有数据清洗但无系统化 ETL |
| **数据输出** | 曝光量/时长统计、目标人群画像、地理分布图、可视化图表、效果报告、原始数据导出 | ✅ 有归因报告 + demo 可视化 |
| **数据呈现** | 多样化呈现（曝光情况、用户画像、广告效果） | ✅ bus-demo.html + demo.html |

---

## 四、AIAdPlacer 对标优化方案

### 4.1 P0 优先级（必须对齐标准）

#### 新增数据模型

```python
# 新增字段到 BusRoute / MediaResources
exposure_duration: Float       # 平均曝光时长（秒）— 标准 T_exposure
ad_duration: Float             # 单广告片时长（秒）— 标准 T_ad
sot: Float                     # 时间占比（Share of Time）
ad_slots_per_cycle: Integer    # 轮播周期内广告数量
flow_otc: Float               # 流动曝光概率（标准公式2）
dwell_otc: Float              # 驻留曝光概率（标准公式4）

# 新增字段到 BusAttribution / Attribution
flow_impressions: Integer      # 流动曝光量（标准公式1）
dwell_impressions: Integer     # 驻留曝光量（标准公式3）
effective_impressions: Integer # 有效曝光量
impression_multiplier: Float   # 曝光乘数（标准公式6）
frequency: Float               # 接触频次
independent_audience: Integer  # 独立受众数量
```

#### 新增曝光计算引擎

```python
class StandardImpressionEngine:
    """基于 T/CCSA 738-2025 标准的曝光量计算引擎"""
    
    def calc_flow_otc(self, exposure_t: float, ad_t: float) -> float:
        """公式(2): 流动曝光概率"""
        return (max(exposure_t, ad_t) - ad_t) / max(exposure_t, 2.0)
    
    def calc_flow_imp(self, flow_otc: float, sot: float, traffic: int) -> float:
        """公式(1): 流动曝光量"""
        return flow_otc * sot * traffic
    
    def calc_dwell_otc(self, exposure_t: float) -> float:
        """公式(4): 驻留曝光概率（5分钟=300秒）"""
        return exposure_t / 300.0
    
    def calc_dwell_imp(self, dwell_otc: float, traffic: int) -> float:
        """公式(3): 驻留曝光量"""
        return dwell_otc * traffic
    
    def calc_total_imp(self, flow_imp: float, dwell_imp: float) -> float:
        """公式(5): 总曝光量"""
        return flow_imp + dwell_imp
    
    def calc_impression_multiplier(self, flow_traffic: int, imp: float, ad_slots: int) -> float:
        """公式(6): 曝光乘数"""
        return (flow_traffic * imp) / ad_slots if ad_slots > 0 else 0.0
    
    def calc_frequency(self, effective_impressions: int, independent_audience: int) -> float:
        """接触频次 = 有效展示次数 / 独立受众数量"""
        return effective_impressions / independent_audience if independent_audience > 0 else 0.0
```

### 4.2 P1 优先级（增强标准能力）

| 优化项 | 说明 | 对应标准 |
|--------|------|----------|
| **迪杰斯特拉路径优化** | 用于地铁/机场/公交枢纽场域的人群最短路径计算 | 标准 7.1 |
| **流动/驻留人群分类** | 基于停留时间区分流动（行走）和驻留（停留>5min）人群 | 标准 7.2 |
| **SOT 时间占比计算** | 根据广告轮播 schedule 计算每个广告的时间占比 | 标准 7.3 |
| **数据源扩展** | 接入运营商 LBS 数据、天气数据、交通流量数据 | 标准 6.1 |

### 4.3 P2 优先级（长期规划）

| 优化项 | 说明 | 对应标准 |
|--------|------|----------|
| **机场场域模型** | 高人流量+高流动性场景的特殊曝光计算 | 标准 A.3 |
| **地铁场域模型** | 有向带权图 + O/D 矩阵 + 迪杰斯特拉最短路径 | 标准 A.1 |
| **隐私合规增强** | 数据采集/处理全流程合规（参考标准 A.3.3） | 标准 A.3.3 |

---

## 五、AIAdPlacer 已有能力 vs 标准差距

### ✅ 已覆盖的标准能力

| 标准能力 | AIAdPlacer 实现 | 文件位置 |
|----------|-----------------|----------|
| 程序化广告投放流程 | FastAPI + LangGraph 编排 | `backend/app/main.py`, `backend/app/agents/orchestrator.py` |
| 自动化竞价 | bus-pDOOH 竞价引擎 | `backend/app/bus/services/bidding_engine.py` |
| 效果归因 | 归因引擎（多触点/时空/漏斗） | `backend/app/services/attribution_engine.py` |
| POI 数据交叉比对 | 腾讯地图 + 高德地图 | `backend/app/services/tencent_map.py` |
| 网格热力图 | 500m 网格 + 热力评分 | `backend/app/bus/services/heat_scoring.py` |
| OneID 跨平台打通 | 手机客户信息 + AI 算法 | README 核心创新点 |
| LBS 定位服务 | 腾讯地图 WebService API | `backend/app/services/tencent_map.py` |

### 🔴 需补充的标准能力

| 标准能力 | 缺失原因 | 补充优先级 |
|----------|----------|------------|
| 流动/驻留曝光分类 | 现有模型未区分人群行为类型 | P0 |
| SOT 时间占比 | 未引入广告轮播时间分配概念 | P0 |
| 曝光乘数 | 现有归因无此指标 | P0 |
| 迪杰斯特拉路径算法 | 热力评分用 POI 密度但无路径优化 | P1 |
| 接触频次 (Frequency) | 有曝光量但无频次计算 | P0 |
| 运营商数据接入 | 用地图 API 替代运营商数据 | P1 |
| 天气/交通数据 | 未集成外部天气/交通 API | P2 |

---

## 六、实施路线图

| 阶段 | 内容 | 交付物 | 时间 |
|------|------|--------|------|
| **v2.1** | 新增流动/驻留曝光模型 + SOT + 曝光乘数 + 接触频次 | 数据模型迁移 + 计算引擎 | Week 1-2 |
| **v2.2** | 迪杰斯特拉路径优化 + 流动/驻留人群分类 | 路径算法 + 人群分类 API | Week 3-4 |
| **v2.3** | 运营商数据接入 + 天气/交通 API 集成 | 数据源扩展 | Week 5-6 |
| **v3.0** | 地铁/机场场域模型 + 隐私合规增强 | 场域专用计算模块 | v3.0 |

---

## 七、合规声明

AIAdPlacer 在数据采集和处理环节遵循以下原则（对标标准 A.3.3）：

1. **数据采集**：不侵犯用户隐私权，所有位置数据经用户授权
2. **数据处理**：OneID 使用 Hash 化标识符，不存储原始手机号/MAC
3. **数据导出**：所有输出数据结构化、清晰化呈现（标准 6.2.3）
4. **审计追踪**：完整记录曝光测量计算过程和数据来源

---

*文档生成日期：2026-05-31*  
*适配标准：T/CCSA 738—2025 / T/CAAAD 040—2025*  
*AIAdPlacer 版本：v2.0 → v2.1 升级规划*
