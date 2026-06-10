# AIAdPlacer MCP 知识库模块

## 📚 概述

MCP 知识库模块自动归档所有外部 MCP 调用结果，支持按日期/工具类型/城市分类存储，提供全文检索与调用日志追踪功能。

## 🗂️ 存储架构

```
data/knowledge/
├── YYYY-MM-DD/                  # 按日期分类
│   ├── pdooh_query_screens/     # 按工具名分类
│   │   ├── 广州市.json           # 按关键参数分类
│   │   └── 深圳市.json
│   ├── pdooh_audience_insight/
│   └── pdooh_create_campaign/
├── index.json                   # 全局索引 (record_id → file)
├── stats.json                   # 知识库统计 (按工具/日期计数)
└── call_logs.jsonl              # 调用日志 (JSONL 格式, 每条独立行)
```

## 🔧 核心功能

### 1. 自动归档
每次 MCP 调用后，自动将结果存储到 `data/knowledge/YYYY-MM-DD/工具名/` 目录。

### 2. 调用日志
JSONL 格式记录每次调用的：
- 工具名、参数、结果摘要
- 调用时间、来源 IP、User-Agent
- 完整结果（通过详情 API 查看）

### 3. 全文检索
支持按工具名、日期范围、城市、关键词检索知识库。

### 4. 统计分析
实时统计：总调用次数、按工具分布、按日期分布。

## 📋 API 接口

### 调用日志

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v2/knowledge/logs` | 调用日志列表（分页） |
| GET | `/api/v2/knowledge/logs/{log_id}` | 调用详情（含完整 result） |
| GET | `/api/v2/knowledge/logs/stats` | 调用统计 |

### 知识库

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v2/knowledge/knowledge/search` | 按工具/日期/城市/关键词检索 |
| GET | `/api/v2/knowledge/knowledge/record/{id}` | 获取完整记录 |
| GET | `/api/v2/knowledge/knowledge/dates` | 列出有数据的日期 |
| GET | `/api/v2/knowledge/knowledge/tools` | 列出工具名 |
| GET | `/api/v2/knowledge/knowledge/date/{date}` | 按日期浏览 |
| GET | `/api/v2/knowledge/knowledge/tool/{name}` | 按工具浏览 |
| GET | `/api/v2/knowledge/knowledge/stats` | 知识库统计 |

## 🐍 Python 使用示例

```python
from app.services.knowledge_base import kb, auto_store_mcp_result

# 自动归档 MCP 调用结果
result = auto_store_mcp_result(
    tool_name="pdooh_query_screens",
    arguments={"city": "广州", "district": "天河区"},
    result=[{"id": 1, "name": "天河城屏"}],
    ip="127.0.0.1",
    user_agent="TestClient/1.0",
)

# 检索知识库
records = kb.search(tool_name="pdooh_query_screens", city="广州", limit=10)

# 获取调用日志
logs = kb.get_call_logs(tool_name="pdooh_query_screens", date_from="2026-06-09", limit=50)
```

## 📊 演示页面

启动后端后访问 `backend/knowledge-demo.html`：

- **调用日志 Tab**：展示每次 MCP 调用的参数、结果摘要、来源 IP
- **知识库 Tab**：按日期/工具浏览、全文检索、统计看板

## 🔍 检索优化

- 全文搜索通过 JSON 序列化匹配参数和结果内容
- 支持日期范围筛选（`date_from` / `date_to`）
- 支持工具名、城市精准过滤
- 调用日志按时间倒序（最新在前）

## 🧹 数据维护

- 知识库文件按日期/工具自动分类，便于清理
- JSONL 调用日志支持分页加载，避免大文件内存问题
- 全局索引仅存储元数据，不存储完整结果

## 📈 统计指标

| 指标 | 说明 |
|------|------|
| `total_records` | 总归档记录数 |
| `by_tool` | 各工具调用次数分布 |
| `by_date` | 各日期调用次数分布 |
| `last_updated` | 最后更新时间 |

## 🚀 部署说明

1. 知识库目录 `data/knowledge/` 会在首次调用时自动创建
2. 调用日志和知识归档在同一事务中完成
3. 归档失败不影响 MCP 调用结果返回（仅记录警告日志）
