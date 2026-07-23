# 增量 PRD：roi_estimate 真实化（L9 价值分析）

## 1. 目标
替换 `indicator_formulas.py:146` 占位 `roi_estimate` 为可解释真实 ROI 模型，打通 `value_index`（综合价值 TOPSIS）真实链路。

## 2. ROI 定义
广告主口径：**真实 ROI = (收益 − 成本) / 成本**。函数返回归一化 **ROI 指数（0–100）** 供聚合；盈亏平衡（ROI=0%）→ 50，ROI≥100% → 100，ROI≤−100% → 0，与其余 0–100 指标对齐。

## 3. 输入字段
- **输入对象**：`row` 为「小区级宽表一行（t_community_wide，由 `generate_indicators` 传入）」，所有指标函数同此约定（见文件头注释 line 7）
- **派生指标**：`daily_reach`、`cpm`、`effect_predict` 经**同模块函数**实时推导，非直接读取 t_poi_indicators 列
  - `daily_reach(row)` = `household_count × occupancy_rate × 2.1`
  - `cpm(row)` = `access_lightbox_price / daily_reach × 1000`
- **原始宽表列**：`access_lightbox_price`（单屏日成本）、`community_id`（P1 跨表关联用）
- **假设常量**：`CVR` 转化率、`AOV` 客单价（模块级写死 + 注释来源）
- **P1 增强**：`contract_amount`（跨表 `t_community.community_id` 关联，宽表已带 community_id）

## 4. 模型草案
- 成本 `cost = cpm × daily_reach / 1000` = `access_lightbox_price`（单屏日投放成本，已验证等价）
- 收益 `revenue = daily_reach × CVR × AOV`
  - `CVR = 0.008`（社区梯媒到店/扫码率 0.5%–2% 取中值，注释来源）
  - `AOV = 80.0 元`（社区周边客单价 50–120 元取中值，注释来源）
- 真实 `ROI = (revenue − cost) / cost`
- **ROI 指数 = clip(ROI × 50 + 50, 0, 100)** 返回 float
- 常量放模块级可调；`effect_predict` 作 P1 校准因子（如 `CVR_eff = CVR × effect_predict/50`）

## 5. 用户故事
- 决策层：希望 `value_index` 按真实 ROI 排序，以按真实价值分配预算。
- 投放优化师：希望看到每屏 ROI 指数与成本/收益拆解，以解释并优化选点。

## 6. 需求池
- **P0**：可解释模型 + 单测 + 4452 行重算分布合理
- **P1**：接入 `contract_amount` 真实成本；与 `effect_predict` 联动校准
- **P2**：在 `schema_constants` / README 标注该算法已真实化

## 7. 验收标准（DoD）
- 函数签名 `roi_estimate(row: dict) -> float` 不变，仅改本函数；参数为模块级常量
- 单测：已知输入 → 已知输出（如 `daily_reach=1000, cpm=20`，其余默认 → 已知指数）
- 4452 行重算：`roi_estimate` 非空、非全 0/全 100、方差合理；`value_index` 随之合理无 NaN/越界
- 现有 15/15 测试不破

## 8. 待确认
1. ROI 比值口径是否认可（已按此设计）？
2. P0 是否暂不接 `contract_amount`（建议 P1）？
3. `CVR`/`AOV` 是否需按社区类型差异化（P1）？
