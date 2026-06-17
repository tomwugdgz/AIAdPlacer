# AIAdPlacer 版本更新说明 v2.1

**发布日期**: 2026-06-17  
**版本号**: v2.1  
**维护人**: AIAdPlacer Team

---

## 📋 更新概述

本次更新主要扩充 MCP 工具数量（8 → 22），新增竞品监测 Agent 服务，完善 API 手册。

---

## 🆕 新增功能

### 1. MCP Server 工具扩充（8 → 22 个）

**新增工具列表：**

| # | 工具名 | 功能 | 数据库 |
|---|--------|------|--------|
| 9 | `pdooh_query_local_screens` | 查询社区智能屏点位 | 单元门智能框架.db |
| 10 | `pdooh_query_local_stats` | 查询城市媒体资源统计 | 单元门智能框架.db |
| 11 | `pdooh_search_local_community` | 按楼盘名搜索社区 | 单元门智能框架.db |
| 12 | `pdooh_query_access_points` | 查询门禁点位（66,308条） | 门禁全国点位.db |
| 13 | `pdooh_query_smart_frames` | 查询单元门点位（8,114条） | 单元门智能框架.db |
| 14 | `pdooh_query_daocha_points` | 查询道闸点位（1,021条） | 广州道闸.db |
| 15 | `pdooh_query_led_points` | 查询LED点位（1,365条） | 商场LED.db |
| 16 | `pdooh_query_elevator_frames` | 查询电梯框架（预留） | 待接入 |
| 17 | `pdooh_query_smart_screen_2025` | 智能屏2025数据（4,488条） | 待接入 |
| 18 | `pdooh_query_shadow_points` | 查询投影屏（预留） | 待接入 |
| 19 | `pdooh_query_city_resources` | 城市资源统计 | 多库联合 |
| 20 | `pdooh_query_city_summary` | 全国城市汇总（217+城市） | 单元门智能框架.db |
| 21 | `pdooh_query_customers` | 查询客户通讯录（26,895条） | 待接入 |
| 22 | `pdooh_calc_roi` | 计算ROI三场景 | 内存计算 |

**技术说明：**
- 工具 9-15、19-20 已接入真实 SQLite 数据库
- 工具 16-17、21 接口已定义，数据接入中
- 工具 22（ROI计算）内置完整计算公式（UV/记忆/转化/LTV/ROI）

### 2. 竞品监测 Agent（端口 5005）

**新增文件：** `backend/competitor_agent.py`

**API 端点：**
- `GET /health` — 健康检查
- `GET /api/competitors` — 竞品数据库查询（按行业筛选）
- `GET /api/pricing` — 竞品定价对比
- `GET /api/intelligence` — 市场情报查询（按行业/品牌筛选）
- `GET /api/intelligence/stats` — 情报统计
- `GET /api/industries` — 行业分类列表
- `GET /api/brands` — 重点品牌列表
- `GET /api/intelligence/search` — 情报搜索

**启动方式：**
```bash
cd backend
python competitor_agent.py
# 或
uvicorn competitor_agent:app --host 0.0.0.0 --port 5005 --reload
```

### 3. 文档更新

- `docs/MCP-Tool-Calling-Guide.md` — 优化版 MCP 工具调用手册（修复 curl 换行符、增加 Python 示例）
- `docs/ROI-Agent-User-Guide.md` — 优化版 ROI Agent 调用指南（增加计算公式详解、商务应用建议）
- `docs/AIAdPlacer-Product-Specification-v2.md` — 增强版产品规格书（含算法公式+完整代码）
- `docs/AIAdPlacer-User-Manual.md` — 用户使用说明书（面向实际操作者）

---

## 🔧 改进与优化

### MCP 工具实现增强
- 原有 8 个工具的 mock 数据保留，新增工具接入真实数据库
- 统一数据库连接管理（`get_sqlite_conn` / `query_to_dicts` 辅助函数）
- 增加异常处理，避免因单个工具失败影响整体服务

### Skill YAML 更新
- `skill.yaml` 更新至 v2.1，列出全部 22 个工具
- 新增触发词：`亲邻科技`、`ROI计算`
- 新增调用示例（查询门禁点位、ROI计算）

### 健康检查接口增强
- 返回字段新增 `version`（当前 v2.1）
- `tools_count` 更新为 22

---

## 🐛 问题修复

- 修复 `pdooh_mcp.py` 中 `mcp_tools_call` 函数缩进错误（原第 213 行 `try` 语句缩进不正确）
- 修复 curl 命令在文档中的换行符显示问题
- 统一术语（记忆人数 → 品牌记忆人数、收益率 → ROI）

---

## 📦 数据库变更

**新增/确认数据库文件：**
- `亲邻单元门智能框架.db` — 8,176 条记录 ✅
- `亲邻门禁全国点位.db` — 66,450 条记录 ✅
- `亲邻广州道闸.db` — 1,021 条记录 ✅
- `亲邻商场LED.db` — 1,365 条记录 ✅

**待接入数据库：**
- 智能屏2025数据（4,488条）— 接口已定义
- 客户通讯录（26,895条）— 接口已定义
- 电梯框架数据 — 预留接口
- 投影屏数据 — 预留接口

---

## 🚀 部署说明

### 更新步骤

1. **拉取最新代码**
   ```bash
   git pull origin master
   ```

2. **更新依赖**（如有新增）
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **重启 MCP Server（端口 5002）**
   ```bash
   # 如果使用了 watchdog.py 守护进程，会自动重启
   # 否则手动重启
   kill $(lsof -t -i:5002)
   python backend/run.py
   ```

4. **启动竞品监测 Agent（端口 5005）**
   ```bash
   cd backend
   python competitor_agent.py &
   ```

### Docker 部署（如适用）

更新 `docker-compose.yml`，新增竞品监测 Agent 服务：

```yaml
  competitor-agent:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python competitor_agent.py
    ports:
      - "5005:5005"
    networks:
      - aiadplacer-network
```

---

## 📊 兼容性说明

- **向后兼容**：原有 8 个 MCP 工具的接口和参数保持不变
- **新增工具**：22 个工具全部通过 MCP 协议暴露，外部 AI Agent 可直接调用
- **竞品 Agent**：独立服务，不影响现有服务（端口 5002-5004）

---

## 🔜 下一步计划

1. **数据接入：**
   - 接入智能屏2025数据（4,488条）
   - 接入客户通讯录数据（26,895条）
   - 接入电梯框架和投影屏数据

2. **新服务创建：**
   - Tom Agent（端口 5003）独立服务
   - ROI Agent（端口 5004）独立服务

3. **功能增强：**
   - MCP 工具返回数据增加 GPS 坐标字段
   - 竞品监测 Agent 接入真实数据源（爬虫/API）
   - 增加 MCP 工具调用频率限制

---

## 📞 联系方式

| 事项 | 信息 |
|------|------|
| 商务咨询 | Tom `17665188615` |
| 媒体方 | 亲邻传媒 |
| 技术支持 | 通过商务联系人转接 |

---

*更新日期：2026-06-17*
