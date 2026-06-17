# AIAdPlacer 版本更新说明 v2.5.0

## 📅 发布日期
2026-06-17

## 🎯 版本主题
**ROI 参数自动调整 + 联动结果可视化**

---

## ✨ 新增功能

### 1. ROI 参数自动调整
**文件**: `backend/app/roi_agent.py`

**功能说明**:
- 根据投放城市自动调整参数（U/β/a/r）
  - 一线城市：U=80, β=0.82, a=30, r_base=0.17
  - 新一线城市：U=100, β=0.85, a=22, r_base=0.18
  - 二线城市：U=110, β=0.87, a=18, r_base=0.19
  - 三线及以下：U=120, β=0.90, a=15, r_base=0.20
- 根据产品类型自动调整参数（r/a/f）
  - 日化：r_mult=1.0, a_base=25, f_mult=1.1
  - 食品：r_mult=1.1, a_base=15, f_mult=1.2
  - 家电：r_mult=0.9, a_base=50, f_mult=0.8
  - 母婴：r_mult=1.2, a_base=35, f_mult=1.3
  - 汽车：r_mult=0.8, a_base=100, f_mult=0.6
- 新增 API 参数：
  - `city`: 投放城市（用于自动调整参数）
  - `product`: 产品类型（用于自动调整参数）
  - `auto_adjust`: 是否自动调整参数（默认 True）

**使用示例**:
```bash
# 传入 city 和 product，自动调整参数
curl "http://127.0.0.1:5004/api/v2/roi/three-scenarios?N=5000&cost=100000&T=14&city=广州&product=黑人牙膏"

# 返回结果包含 auto_adjusted=True，以及调整说明
```

---

### 2. 联动结果可视化
**文件**: `backend/app/tom_agent.py`

**功能说明**:
- Tom Agent 生成投放方案时，自动调用 ROI Agent 计算三场景 ROI
- 在返回结果里增加 `roi_visualization` 字段，包含 ROI 可视化图表的 HTML
- 可视化图表包含：
  - ROI 三场景条形图（悲观/中性/乐观）
  - LTV 对比（三场景）
  - 计算说明（公式 + 数据来源）

**可视化图表示例**:
```html
<div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
    <h3>📊 ROI 三场景预测</h3>
    <!-- ROI 条形图 -->
    <div style="display: flex; ...">
        <div style="width: {max(pes_roi/5, 2)}%; background: #ff6b6b;"></div>
    </div>
    <!-- LTV 对比 -->
    <div style="display: flex; justify-content: space-around;"></div>
</div>
```

**API 端点**:
- `POST /api/v2/tom/plan/generate`
  - 请求参数增加 `product` 字段
  - 返回结果增加 `roi_visualization` 字段（HTML）

---

## 🔧 改进与优化

### 1. ROI Agent 参数调整逻辑优化
- 修改 `calc_three_scenarios` 函数，支持传入 `r_neutral/a_neutral/f_neutral` 参数
- 修改 `/calculate` 接口，支持 `city` 和 `product` 参数
- 修改 `/three-scenarios` 接口，支持 `city` 和 `product` 参数

### 2. Tom Agent 联动逻辑优化
- 修改 `call_roi_agent` 函数，增加 `product` 参数
- 在 `call_roi_agent` 函数里，生成 ROI 可视化图表 HTML
- 修改 `/plan/generate` 端点，传递 `product` 参数

---

## 🐛 修复问题

### 1. 修复语法错误
- 修复 `compare_scenarios` 函数里的字符串格式化错误（第 630 行）
- 修复 `roi_agent.py` 的语法错误

---

## 📦 部署说明

### 1. 启动服务
**方式一：使用 run_all_agents.py（推荐）**
```bash
cd D:/Mirofish/AIAdPlacer/backend
python run_all_agents.py
```

**方式二：分别启动**
```bash
# 启动 ROI Agent（端口 5004）
cd D:/Mirofish/AIAdPlacer/backend
python -m uvicorn app.roi_agent:router --host 0.0.0.0 --port 5004 --reload

# 启动 Tom Agent（端口 5003）
cd D:/Mirofish/AIAdPlacer/backend
python -m uvicorn app.tom_agent:router --host 0.0.0.0 --port 5003 --reload
```

### 2. 测试联动功能
**测试 ROI 参数自动调整**:
```bash
# 测试城市参数调整
curl "http://127.0.0.1:5004/api/v2/roi/three-scenarios?N=5000&cost=100000&T=14&city=广州&product=黑人牙膏"

# 返回结果应包含 auto_adjusted=True，以及调整说明
```

**测试联动结果可视化**:
```bash
# 测试 Tom Agent 生成方案（含 ROI 可视化）
curl -X POST http://127.0.0.1:5003/api/v2/tom/plan/generate \
  -H "Content-Type: application/json" \
  -d '{"brand":"黑人牙膏","product":"双重薄荷牙膏","budget":100000,"cities":["广州"]}'

# 返回结果应包含 roi_visualization 字段（HTML）
```

---

## 📊 测试覆盖

| 功能 | 测试状态 | 说明 |
|------|----------|------|
| ROI 参数自动调整（城市） | ✅ 待测试 | 需启动 ROI Agent 测试 |
| ROI 参数自动调整（产品） | ✅ 待测试 | 需启动 ROI Agent 测试 |
| 联动结果可视化 | ✅ 待测试 | 需启动 Tom Agent + ROI Agent 测试 |
| Tom Agent 生成方案 | ✅ 待测试 | 需启动 Tom Agent 测试 |

---

## 🚀 下一步计划

1. **前端界面开发**
   - 开发 ROI 可视化图表前端组件（使用 Chart.js 或 ECharts）
   - 开发 Tom Agent 对话界面（集成 ROI 可视化图表）

2. **参数调整优化**
   - 根据实际投放数据，优化城市/产品参数映射
   - 增加更多产品类型的参数映射

3. **联动功能增强**
   - 在 Tom Agent 对话里，实时显示 ROI 计算结果
   - 支持用户动态调整参数，实时更新 ROI 计算结果

---

## 📝 附录：参数调整映射表

### 城市参数映射

| 城市等级 | 城市列表 | U（户/栋） | β（接触率） | a（客单价） | r_base（记忆率） |
|---------|----------|------------|------------|------------|----------------|
| 一线城市 | 北京/上海/广州/深圳 | 80 | 0.82 | 30 | 0.17 |
| 新一线城市 | 成都/杭州/重庆/... | 100 | 0.85 | 22 | 0.18 |
| 二线城市 | 昆明/福州/无锡/... | 110 | 0.87 | 18 | 0.19 |
| 三线及以下 | 其他城市 | 120 | 0.90 | 15 | 0.20 |

### 产品类型参数映射

| 产品类型 | 关键词 | r_mult（记忆率倍数） | a_base（客单价） | f_mult（复购系数倍数） |
|---------|--------|---------------------|-----------------|----------------------|
| 日化 | 牙膏/洗发水/... | 1.0 | 25 | 1.1 |
| 食品 | 食品/零食/... | 1.1 | 15 | 1.2 |
| 家电 | 电视/冰箱/... | 0.9 | 50 | 0.8 |
| 母婴 | 母婴/奶粉/... | 1.2 | 35 | 1.3 |
| 汽车 | 汽车/新能源车/... | 0.8 | 100 | 0.6 |
| 其他 | - | 1.0 | 22 | 1.0 |

---

## 📞 联系方式

- 技术支持：Tom（17665188615）
- 项目地址：<a href="https://github.com/tomwugdgz/AIAdPlacer">GitHub</a> | <a href="https://gitee.com/duckwolf/AIAdPlacer">Gitee</a> | <a href="https://gitcode.com/duckwolf/AIAdPlacer">GitCode</a>

---

**AIAdPlacer 团队**  
2026-06-17
