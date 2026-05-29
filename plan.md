# pDOOH 前端Demo + 后端API + A2A MCP接口 实施计划

## 目标
1. 改造 `demo.html`，连接真实数据库，替换所有模拟数据
2. 搭建后端REST API（FastAPI），对接 `pdooh` 数据库
3. 提供 A2A 接口（MCP Server + Skill模块），让外部AI Agent可调用投放能力

## 数据库现状（pdooh）
- PostgreSQL: 127.0.0.1:5432, DB: `pdooh`, User: `quantdinger`, Password: `quantdinger123`
- 核心表：screen(9801屏), person_anchor(500人), trusted_id_binding, spatial_trajectory, poi_data(13362条), vw_screen_audience
- 扩展标签：extended_dmp_tags(55维度), person_dmp_tags

## 实施步骤

### Step 1: 后端API（FastAPI）
文件：`backend/app/pdooh_api.py`（新建）

端点设计：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v2/pdooh/screens | 查询智能屏列表（支持经纬度/半径筛选） |
| GET | /api/v2/pdooh/screens/{id} | 单屏详情 + 人群画像（vw_screen_audience） |
| GET | /api/v2/pdooh/persons | 查询人锚点列表 |
| GET | /api/v2/pdooh/persons/{id}/tags | 某人DMP标签 |
| GET | /api/v2/pdooh/persons/{id}/trajectory | 某人轨迹 + 触屏记录 |
| GET | /api/v2/pdooh/poi | POI列表（按类别/距离筛选） |
| GET | /api/v2/pdooh/screens/{id}/audience | 单屏受众分析（年龄/性别/兴趣分布） |
| POST | /api/v2/pdooh/campaigns | 创建投放计划 |
| GET | /api/v2/pdooh/campaigns | 投放计划列表 |

### Step 2: 改造 demo.html
文件：`demo.html`（原地改造）

替换内容：
- 模拟屏数据 → 调用 `GET /api/v2/pdooh/screens?lat=...&lng=...&radius=...`
- 模拟人群画像 → 调用 `GET /api/v2/pdooh/screens/{id}/audience`
- 模拟POI → 调用 `GET /api/v2/pdooh/poi?lat=...&lng=...`
- 保留腾讯地图展示逻辑（已集成）

### Step 3: A2A MCP接口（MCP Server）
文件：`backend/app/bmn/pdooh_mcp.py`（新建）

提供MCP Tools：
- `search_screens` - 按位置/标签搜索智能屏
- `get_screen_audience` - 获取某屏人群画像
- `create_campaign` - 创建投放计划
- `query_person_tags` - 查询某人DMP标签（可信ID）
- `match_audience_targeting` - AI人群定向匹配

MCP Server 注册到现有 FastAPI 应用，路径：`/api/v2/mcp/pdooh`

### Step 4: Skill调用模块
文件：`~/.workbuddy/skills/pdooh-agent/SKILL.md`（新建Skill）

封装 pDOOH 投放能力为 WorkBuddy Skill，支持：
- 自然语言查询屏： "广州天河区有哪些屏覆盖25-35岁女性？"
- 创建投放计划： "帮我创建一个投放计划，目标人群是母婴人群..."
- 人群洞察： "分析北京路商圈屏的受众画像"

## 文件变更清单
| 文件 | 操作 |
|------|------|
| `backend/app/pdooh_api.py` | 新建 |
| `backend/app/main.py` | 修改（注册pdooh路由） |
| `backend/app/bmn/pdooh_mcp.py` | 新建 |
| `demo.html` | 修改（替换模拟数据为API调用） |
| `~/.workbuddy/skills/pdooh-agent/SKILL.md` | 新建 |

## 验证方式
1. 启动后端：`cd backend && uvicorn app.main:app --port 5002`
2. 访问 Swagger：`http://localhost:5002/docs`
3. 打开 `demo.html`，确认地图展示真实屏数据
4. 测试 MCP 接口：`GET /api/v2/mcp/pdooh/tools`
