# 🚀 BabyAGI (5006端口) 使用指南

> **服务地址**：http://localhost:5006  
> **版本**：v1.0

---

## 一、接口总览

| 接口 | 方法 | 功能 |
|:-----|:-----|:-----|
| `/health` | GET | 健康检查 |
| `/api/task/add` | POST | 添加任务 |
| `/api/task/execute/<task_id>` | POST | 执行任务 |
| `/api/tasks` | GET | 查看所有任务 |
| `/api/demo` | GET | 演示模式 |

---

## 二、任务类型（支持的功能）

| 任务关键词 | 功能 | 返回示例 |
|:-----------|:-----|:---------|
| `查询XX单元门` | 查询单元门点位 | 返回楼盘数据 |
| `查询XX门禁` | 查询门禁点位 | 返回楼盘数据 |
| `查询XX智能屏` | 查询智能屏点位 | 返回楼盘数据 |
| `查询XX城市汇总` | 查询城市资源统计 | 返回汇总数据 |
| `搜索XX社区` | 搜索社区楼盘 | 返回匹配楼盘 |
| `查询XX客户` | 查询客户资料 | 返回客户列表 |
| `ROI计算` | ROI投资回报计算 | 返回ROI数据 |
| `生成XX方案` | 生成投放方案 | 返回完整方案 |

---

## 三、详细接口说明

### 3.1 健康检查

```bash
curl http://localhost:5006/health
```

**响应**：
```json
{
  "service": "pDOOH BabyAGI",
  "status": "ok",
  "version": "v1.0"
}
```

---

### 3.2 添加任务

**请求**：
```bash
curl -X POST http://localhost:5006/api/task/add \n  -H "Content-Type: application/json" \n  -d '{"description": "查询广州单元门点位"}'
```

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| `description` | string | ✅ | 任务描述，支持中文 |

**支持的描述格式**：

| 描述示例 | 解析结果 |
|:---------|:---------|
| `查询广州单元门点位` | 城市=广州, 功能=单元门查询 |
| `查询深圳门禁点位` | 城市=深圳, 功能=门禁查询 |
| `查询成都智能屏点位` | 城市=成都, 功能=智能屏查询 |
| `查询东莞门禁` | 城市=东莞, 功能=门禁查询 |
| `ROI计算 5000框两周` | 功能=ROI计算 |
| `生成比亚迪广州50万方案` | 品牌=比亚迪, 城市=广州, 预算=50万 |

**响应**：
```json
{
  "status": "success",
  "task": {
    "id": "1",
    "description": "查询广州单元门点位",
    "status": "pending",
    "result": null
  }
}
```

---

### 3.3 执行任务

**请求**：
```bash
curl -X POST http://localhost:5006/api/task/execute/1
```

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| `task_id` | string | ✅ | 任务ID（从add接口获取） |

**响应**：
```json
{
  "status": "success",
  "result": {
    "id": "1",
    "description": "查询广州单元门点位",
    "status": "completed",
    "result": {
      "status": "success",
      "count": 10,
      "sample": "利雅湾"
    }
  }
}
```

---

### 3.4 查看所有任务

**请求**：
```bash
curl http://localhost:5006/api/tasks
```

**响应**：
```json
{
  "status": "success",
  "tasks": [
    {
      "id": "1",
      "description": "查询广州单元门点位",
      "status": "completed",
      "result": {...}
    },
    {
      "id": "2",
      "description": "查询深圳门禁点位",
      "status": "completed",
      "result": {...}
    }
  ]
}
```

---

### 3.5 演示模式

**请求**：
```bash
curl http://localhost:5006/api/demo
```

**功能**：自动创建并执行3个任务：
1. 查询广州单元门点位
2. 查询深圳门禁点位
3. 查询成都智能屏点位

---

## 四、完整调用示例

### 4.1 单任务调用

```bash
# Step 1: 添加任务
curl -X POST http://localhost:5006/api/task/add \n  -H "Content-Type: application/json" \n  -d '{"description": "查询广州单元门点位"}'

# Step 2: 执行任务（假设返回的id是1）
curl -X POST http://localhost:5006/api/task/execute/1

# Step 3: 查看任务结果
curl http://localhost:5006/api/tasks
```

---

### 4.2 多任务串联

```bash
# 添加并执行多个任务
for desc in "查询广州单元门" "查询深圳门禁" "查询东莞门禁" "查询佛山单元门" "ROI计算"; do
  task=$(curl -s -X POST http://localhost:5006/api/task/add \n    -H "Content-Type: application/json" \n    -d "{"description": "$desc"}")
  task_id=$(echo $task | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
  curl -s -X POST "http://localhost:5006/api/task/execute/$task_id"
done
```

---

### 4.3 Python调用示例

```python
import requests
import json

BASE_URL = "http://localhost:5006"

def add_task(description):
    """添加任务"""
    response = requests.post(
        f"{BASE_URL}/api/task/add",
        json={"description": description}
    )
    return response.json()["task"]["id"]

def execute_task(task_id):
    """执行任务"""
    response = requests.post(f"{BASE_URL}/api/task/execute/{task_id}")
    return response.json()

def get_tasks():
    """获取所有任务"""
    response = requests.get(f"{BASE_URL}/api/tasks")
    return response.json()

# 示例：分析比亚迪华南区投放
tasks = [
    "查询广州单元门点位",
    "查询深圳门禁点位",
    "查询东莞门禁点位",
    "查询佛山单元门点位"
]

for desc in tasks:
    task_id = add_task(desc)
    result = execute_task(task_id)
    print(f"✅ {desc}: {result['result']['result']}")
```

---

## 五、支持的关键词

### 5.1 城市关键词

| 关键词 | 解析 |
|:-------|:-----|
| `广州` | 广东省会 |
| `深圳` | 广东省 |
| `东莞` | 广东省 |
| `佛山` | 广东省 |
| `珠海` | 广东省 |
| `中山` | 广东省 |
| `北京` | 首都 |
| `上海` | 直辖市 |
| `成都` | 四川省 |
| `重庆` | 直辖市 |
| `杭州` | 浙江省 |
| `南京` | 江苏省 |
| `武汉` | 湖北省 |
| `西安` | 陕西省 |
| `天津` | 直辖市 |

### 5.2 功能关键词

| 关键词 | 功能 |
|:-------|:-----|
| `单元门` | 单元门灯箱点位查询 |
| `门禁` | 门禁点位查询 |
| `智能屏` | 智能屏点位查询 |
| `社区` | 社区楼盘搜索 |
| `客户` | 客户资料查询 |
| `城市汇总` | 城市资源统计 |
| `ROI` / `roi` | ROI投资回报计算 |
| `方案` / `计划` | 投放方案生成 |

---

## 六、返回值说明

### 6.1 任务状态

| 状态 | 说明 |
|:-----|:-----|
| `pending` | 等待执行 |
| `running` | 执行中 |
| `completed` | 已完成 |
| `failed` | 执行失败 |

### 6.2 结果格式

```json
{
  "status": "success",
  "count": 10,
  "sample": "利雅湾"
}
```

---

## 七、错误处理

### 7.1 任务不存在

```json
{
  "status": "error",
  "message": "Task not found"
}
```

### 7.2 未知任务类型

```json
{
  "status": "unknown_task"
}
```

---

## 八、调用流程图

```
┌─────────────────────────────────────────────────────────────┐
│                     BabyAGI 调用流程                        │
└─────────────────────────────────────────────────────────────┘

Step 1: 添加任务
┌─────────────────────────────────────────────────────────────┐
│  POST /api/task/add                                         │
│  {"description": "查询广州单元门点位"}                       │
│                              ↓