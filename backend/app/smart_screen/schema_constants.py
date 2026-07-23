"""
智能屏资源子系统（Smart Screen L9）— 全系统单一事实来源（Schema Constants）。

本模块集中定义：
1. FOUR_LAYERS      —— 四层架构（输入层 / 关联层 / 算法层 / 产出层）及每层表清单
2. ALGORITHMS       —— 19 条算法注册目录（code/name/category/source/journal_level/
                       validated_city/input_fields/weight/formula_hint/status/description）
3. INDICATOR_CATEGORIES —— 7 大类（A~G）共 39 个产出指标字段名（含中文语义）
4. INDICATOR_COLUMNS     —— 39 个指标字段名的扁平列表（与 t_poi_indicators 列序一致）

所有下游模块（build_db / algorithm_catalog / indicator_formulas / indicators / dao / api）
均从这里取值，禁止在别处硬编码算法或指标定义。

作者: 寇豆码（Kou）
日期: 2026-06-20
"""

from app.smart_screen.ss_config import (
    LAYER_INPUT,
    LAYER_ASSOCIATION,
    LAYER_ALGORITHM,
    LAYER_OUTPUT,
    TABLE_MEDIA,
    TABLE_COMMUNITY,
    TABLE_DEVICE,
    TABLE_DELIVERY,
    TABLE_SALES,
    TABLE_COMMUNITY_WIDE,
    TABLE_ALGORITHM,
    TABLE_INDICATORS,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. 四层架构定义
# ═══════════════════════════════════════════════════════════════════════════════

FOUR_LAYERS = {
    LAYER_INPUT: {
        "name": "输入层",
        "desc": "4 孤岛原始数据：媒体列表（真实 xls）+ 小区/设备/投放/销售（派生占位）",
        "tables": [
            TABLE_MEDIA,
            TABLE_COMMUNITY,
            TABLE_DEVICE,
            TABLE_DELIVERY,
            TABLE_SALES,
        ],
    },
    LAYER_ASSOCIATION: {
        "name": "关联层",
        "desc": "5 纽带（户数/入住率/楼栋/设备/投放）JOIN 成小区级宽表",
        "tables": [TABLE_COMMUNITY_WIDE],
    },
    LAYER_ALGORITHM: {
        "name": "算法层",
        "desc": "19 个算法注册位（当前仅注册元数据，逻辑占位待真实模型替换）",
        "tables": [TABLE_ALGORITHM],
    },
    LAYER_OUTPUT: {
        "name": "产出层",
        "desc": "7 大类共 39 指标（小区级 / 点位级）",
        "tables": [TABLE_INDICATORS],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. 19 算法注册目录（按文档附录 A）
#    每个算法字段：
#      code          算法编码 (ALG_XXX)
#      name          算法名称（中文）
#      category      所属产出大类 A~D（E/F/G 由宽表直接启发式生成，不逐项对应）
#      source        学术来源
#      journal_level 期刊级别
#      validated_city 验证城市
#      input_fields  使用的宽表字段（list，JSON 序列化存储于 t_algorithm）
#      weight        加权权重
#      formula_hint  示意公式（占位）
#      status        注册状态，统一 'registered'
#      description   中文说明
# ═══════════════════════════════════════════════════════════════════════════════

ALGORITHMS = [
    # ── A. 人口覆盖（5）──────────────────────────────────────────────────────
    {
        "code": "ALG_POP_REACH",
        "name": "日均触达",
        "category": "A",
        "source": "城市户外广告受众测量模型",
        "journal_level": "CSSCI",
        "validated_city": "广州",
        "input_fields": ["household_count", "occupancy_rate"],
        "weight": 1.0,
        "formula_hint": "daily_reach = household_count * occupancy_rate * 2.1",
        "status": "registered",
        "description": "基于小区户数与入住率估算日均广告触达人次。",
    },
    {
        "code": "ALG_POP_DEPTH",
        "name": "楼栋深度",
        "category": "A",
        "source": "社区媒体触达深度模型",
        "journal_level": "CSSCI",
        "validated_city": "深圳",
        "input_fields": ["building_count"],
        "weight": 0.8,
        "formula_hint": "building_depth = min(100, building_count * 3.5)",
        "status": "registered",
        "description": "以楼栋数量刻画触达在小区内的纵向深度。",
    },
    {
        "code": "ALG_POP_DUAL",
        "name": "双触点",
        "category": "A",
        "source": "多触点整合曝光理论",
        "journal_level": "SSCI Q1",
        "validated_city": "北京",
        "input_fields": ["gate_device_count", "access_device_count", "household_count"],
        "weight": 0.9,
        "formula_hint": "dual_touch = min(100, (gate+access)/household*10000)",
        "status": "registered",
        "description": "大门 + 门禁双触点整合曝光强度。",
    },
    {
        "code": "ALG_POP_COVER",
        "name": "覆盖率",
        "category": "A",
        "source": "覆盖率测算方法",
        "journal_level": "—",
        "validated_city": "上海",
        "input_fields": ["occupancy_rate", "building_count"],
        "weight": 1.0,
        "formula_hint": "coverage_rate = min(100, occupancy*100*(1-1/(1+building)))",
        "status": "registered",
        "description": "小区常住人口的广告有效覆盖率。",
    },
    {
        "code": "ALG_POP_INDEX",
        "name": "人口指数",
        "category": "A",
        "source": "人口密度与触达指数",
        "journal_level": "CSCD",
        "validated_city": "成都",
        "input_fields": ["daily_reach"],
        "weight": 0.7,
        "formula_hint": "population_index = min(100, daily_reach/50)",
        "status": "registered",
        "description": "将日均触达归一化为人口规模相对指数。",
    },
    # ── B. 质量评分（5）──────────────────────────────────────────────────────
    {
        "code": "ALG_Q_HEALTH",
        "name": "健康度",
        "category": "B",
        "source": "设备健康度评估",
        "journal_level": "EI",
        "validated_city": "广州",
        "input_fields": ["monthly_failure_rate"],
        "weight": 1.0,
        "formula_hint": "health_score = max(0, 100 - failure_rate*1000)",
        "status": "registered",
        "description": "由月故障率推导设备整体健康度。",
    },
    {
        "code": "ALG_Q_TIMELY",
        "name": "及时率",
        "category": "B",
        "source": "上刊及时率模型",
        "journal_level": "NSFC",
        "validated_city": "深圳",
        "input_fields": ["historical_launch_count"],
        "weight": 0.9,
        "formula_hint": "timeliness_rate = min(100, 95 + launch*0.5)",
        "status": "registered",
        "description": "历史上刊排期的及时完成率。",
    },
    {
        "code": "ALG_Q_ACTIVE",
        "name": "活跃度",
        "category": "B",
        "source": "广告活跃度指数",
        "journal_level": "SSCI Q1",
        "validated_city": "杭州",
        "input_fields": ["historical_launch_count", "access_device_count"],
        "weight": 0.8,
        "formula_hint": "activity_score = min(100, launch*10 + access*2)",
        "status": "registered",
        "description": "综合上刊频次与门禁设备数的投放活跃度。",
    },
    {
        "code": "ALG_Q_STABLE",
        "name": "稳定性",
        "category": "B",
        "source": "故障率与稳定性",
        "journal_level": "—",
        "validated_city": "武汉",
        "input_fields": ["monthly_failure_rate"],
        "weight": 0.85,
        "formula_hint": "stability_score = max(0, 100 - failure_rate*500)",
        "status": "registered",
        "description": "由故障率反向推导运行稳定性。",
    },
    {
        "code": "ALG_Q_INDEX",
        "name": "质量指数",
        "category": "B",
        "source": "综合质量评估AHP",
        "journal_level": "—",
        "validated_city": "广州",
        "input_fields": ["health_score", "timeliness_rate", "activity_score", "stability_score"],
        "weight": 1.0,
        "formula_hint": "quality_index = mean(health, timely, active, stable)",
        "status": "registered",
        "description": "健康/及时/活跃/稳定四维加权综合质量指数（AHP）。",
    },
    # ── C. 效果预测（4）──────────────────────────────────────────────────────
    {
        "code": "ALG_E_HEAT",
        "name": "行业热度",
        "category": "C",
        "source": "行业搜索热度指数",
        "journal_level": "CSSCI",
        "validated_city": "北京",
        "input_fields": ["covered_industry_count"],
        "weight": 1.0,
        "formula_hint": "industry_heat = min(100, covered*20 + 40)",
        "status": "registered",
        "description": "基于覆盖行业数估算投放行业热度。",
    },
    {
        "code": "ALG_E_RECO",
        "name": "推荐分",
        "category": "C",
        "source": "协同过滤推荐",
        "journal_level": "CCF A",
        "validated_city": "上海",
        "input_fields": ["quality_index", "population_index"],
        "weight": 0.95,
        "formula_hint": "recommend_score = min(100, q*0.5 + pop*0.5)",
        "status": "registered",
        "description": "结合质量与人口指数的协同过滤推荐分。",
    },
    {
        "code": "ALG_E_PEAK",
        "name": "旺季指数",
        "category": "C",
        "source": "季节性销售指数",
        "journal_level": "CSSCI",
        "validated_city": "广州",
        "input_fields": [],
        "weight": 0.8,
        "formula_hint": "peak_season_index = 70 (占位, 待季节模型)",
        "status": "registered",
        "description": "投放季节性旺淡季指数（占位）。",
    },
    {
        "code": "ALG_E_PREDICT",
        "name": "效果预测",
        "category": "C",
        "source": "投放效果回归预测",
        "journal_level": "SSCI Q1",
        "validated_city": "深圳",
        "input_fields": ["recommend_score", "industry_heat"],
        "weight": 1.0,
        "formula_hint": "effect_predict = min(100, reco*0.6 + heat*0.4)",
        "status": "registered",
        "description": "回归模型预估整体投放效果。",
    },
    # ── D. 价值分析（5）──────────────────────────────────────────────────────
    {
        "code": "ALG_V_CPM",
        "name": "CPM",
        "category": "D",
        "source": "CPM定价模型",
        "journal_level": "—",
        "validated_city": "广州",
        "input_fields": ["access_lightbox_price", "daily_reach"],
        "weight": 1.0,
        "formula_hint": "cpm = lightbox_price / daily_reach * 1000",
        "status": "registered",
        "description": "千次触达成本定价模型。",
    },
    {
        "code": "ALG_V_COST",
        "name": "性价比",
        "category": "D",
        "source": "ROI性价比模型",
        "journal_level": "CSSCI",
        "validated_city": "北京",
        "input_fields": ["daily_reach", "ad_door_avg_price"],
        "weight": 0.9,
        "formula_hint": "cost_performance = daily_reach / door_price * 10",
        "status": "registered",
        "description": "单位广告门成本带来的触达性价比。",
    },
    {
        "code": "ALG_V_SSSC",
        "name": "SSSC系数",
        "category": "D",
        "source": "场景-受众-空间-成本模型",
        "journal_level": "—",
        "validated_city": "上海",
        "input_fields": ["occupancy_rate", "building_count", "gate_device_count"],
        "weight": 1.0,
        "formula_hint": "sssc = occupancy*building / gate",
        "status": "registered",
        "description": "场景-受众-空间-成本四维综合系数。",
    },
    {
        "code": "ALG_V_ROI",
        "name": "ROI预估",
        "category": "D",
        "source": "广告ROI归因",
        "journal_level": "—",
        "validated_city": "深圳",
        "input_fields": ["daily_reach", "cpm"],
        "weight": 0.95,
        "formula_hint": "roi_index = clip((reach*CVR*AOV - cost)/cost *50 +50, 0, 100)，cost=CPM*reach/1000；CVR=0.008, AOV=80 为社区梯媒统一假设常量",
        "status": "registered",
        "description": "可解释真实 ROI 模型：收益=日触达×CVR×AOV，成本=CPM×日触达/1000（=单屏日投放成本），真实 ROI=(收益-成本)/成本，映射为 0–100 指数（盈亏平衡→50）。",
    },
    {
        "code": "ALG_V_INDEX",
        "name": "价值指数",
        "category": "D",
        "source": "综合价值TOPSIS",
        "journal_level": "—",
        "validated_city": "广州",
        "input_fields": ["cost_performance", "roi_estimate", "effect_predict"],
        "weight": 1.0,
        "formula_hint": "value_index = mean(cost, roi, effect)",
        "status": "registered",
        "description": "性价比/ROI/效果 TOPSIS 综合价值指数。",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# 3. 产出层 39 指标（7 大类 A~G）
#    每类含：name 中文语义 + columns 字段名列表（与 t_poi_indicators 列序一致）
# ═══════════════════════════════════════════════════════════════════════════════

INDICATOR_CATEGORIES = {
    "A": {
        "name": "人口覆盖",
        "count": 5,
        "columns": [
            ("daily_reach", "日均触达"),
            ("building_depth", "楼栋深度"),
            ("dual_touch", "双触点"),
            ("coverage_rate", "覆盖率"),
            ("population_index", "人口指数"),
        ],
    },
    "B": {
        "name": "质量评分",
        "count": 5,
        "columns": [
            ("health_score", "健康度"),
            ("timeliness_rate", "及时率"),
            ("activity_score", "活跃度"),
            ("stability_score", "稳定性"),
            ("quality_index", "质量指数"),
        ],
    },
    "C": {
        "name": "效果预测",
        "count": 4,
        "columns": [
            ("industry_heat", "行业热度"),
            ("recommend_score", "推荐分"),
            ("peak_season_index", "旺季指数"),
            ("effect_predict", "效果预测"),
        ],
    },
    "D": {
        "name": "价值分析",
        "count": 5,
        "columns": [
            ("cpm", "CPM"),
            ("cost_performance", "性价比"),
            ("sssc_coefficient", "SSSC系数"),
            ("roi_estimate", "ROI预估"),
            ("value_index", "价值指数"),
        ],
    },
    "E": {
        "name": "画像标签",
        "count": 5,
        "columns": [
            ("grade_tag", "档次"),
            ("consumption_power", "消费力"),
            ("commute_tag", "通勤"),
            ("family_tag", "家庭"),
            ("function_tag", "功能"),
        ],
    },
    "F": {
        "name": "空间价值",
        "count": 4,
        "columns": [
            ("integration", "整合度"),
            ("choice", "选择度"),
            ("depth", "深度"),
            ("sci", "SCI"),
        ],
    },
    "G": {
        "name": "行业适配",
        "count": 11,
        "columns": [
            ("fit_takeout", "外卖"),
            ("fit_ecommerce", "电商"),
            ("fit_fmcg", "快消"),
            ("fit_beauty", "美妆"),
            ("fit_auto", "汽车"),
            ("fit_education", "教育"),
            ("fit_realestate", "地产"),
            ("fit_finance", "金融"),
            ("fit_health", "医疗健康"),
            ("fit_travel", "旅游"),
            ("fit_local", "本地生活"),
        ],
    },
}

# 扁平的 39 个指标字段名（与 t_poi_indicators 业务列顺序严格一致，供 INSERT/SELECT 使用）
INDICATOR_COLUMNS: list = []
# 指标字段名 -> 中文语义 映射（供 API 响应双语命名）
INDICATOR_CN_NAMES: dict = {}
for _cat, _info in INDICATOR_CATEGORIES.items():
    for _en, _cn in _info["columns"]:
        INDICATOR_COLUMNS.append(_en)
        INDICATOR_CN_NAMES[_en] = _cn

# 一致性自检：必须恰好 39 个指标
assert len(INDICATOR_COLUMNS) == 39, f"指标数量应为 39，实际 {len(INDICATOR_COLUMNS)}"
assert len(ALGORITHMS) == 19, f"算法数量应为 19，实际 {len(ALGORITHMS)}"

# 四类 A~D 对应 19 算法（E/F/G 由宽表直接启发式生成，不在此映射）
ALGORITHM_CATEGORIES = ["A", "B", "C", "D"]


def algorithm_count() -> int:
    """返回算法总数（恒为 19）。"""
    return len(ALGORITHMS)


def indicator_count() -> int:
    """返回指标总数（恒为 39）。"""
    return len(INDICATOR_COLUMNS)
