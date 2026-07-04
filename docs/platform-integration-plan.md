# 🔗 AIAdPlacer 平台整体调用方案

> **文档版本**：v1.0  
> **创建日期**：2026-07-04  
> **适用版本**：AIAdPlacer v2.0+

---

## 一、平台架构概览

AIAdPlacer 采用 **多端口微服务架构**，各服务独立运行、协同工作：

```
┌─────────────────────────────────────────────────────────────┐
│                    前端展示层                                │
│  web/index.html（AI Copilot 管理台）                       │
│  demo.html（腾讯地图可视化）                                │
│  bus-demo.html（公交线路热力图）                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST / WebSocket / MCP
┌─────────────────────────────────────────────────────────────┐
│              多端口微服务层 (Ports 5002-5006)               │
│                                                             │
│  Port 5002: FastAPI 主服务（MCP Server + 22个工具）        │
│  Port 5003: Tom Agent（CPM 计算 + 投放方案生成）           │
│  Port 5004: ROI Agent（三场景 ROI 计算）                   │
│  Port 5005: 竞品Agent（竞品监控 + 市场情报）               │
│  Port 5006: BabyAGI（任务自动化编排引擎）⭐ 新增           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                    │
│  PostgreSQL (pdooh + ai_adplacer)                         │
│  SQLite (qinlin_local.db - 100,000+ 点位数据)             │
│  Redis (缓存) · ChromaDB (向量检索)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、服务端口与调用方式

### 2.1 端口分配表

| 端口 | 服务名 | 协议 | 核心功能 |
|------|--------|------|----------|
| **5002** | FastAPI 主服务 | REST + MCP | 22个MCP工具、pDOOH API、Agent编排 |
| **5003** | Tom Agent | REST | CPM计算、投放方案生成 |
| **5004** | ROI Agent | REST | 三场景ROI计算（悲观/中性/乐观） |
| **5005** | 竞品Agent | REST | 竞品监控、市场情报搜索 |
| **5006** | BabyAGI | REST | 任务自动化编排、多任务串联 |

### 2.2 服务调用关系图

```
用户/外部AI Agent
    │
    ├──→ Port 5006 (BabyAGI) ──→ 自动化任务编排
    │                            │
    │                            ├──→ Port 5002 (MCP工具调用)
    │                            ├──→ Port 5003 (CPM计算)
    │                            ├──→ Port 5004 (ROI计算)
    │                            └──→ Port 5005 (竞品查询)
    │
    ├──→ Port 5002 (主服务) ────→ 直接调用22个MCP工具
    │
    └──→ Port 5003/5004/5005 ──→ 单独调用各Agent
```

---

## 三、标准调用流程

### 3.1 完整投放流程（6步）

```bash
# Step 1: 查询点位（Port 5002）
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_screens", "arguments": {"city": "广州", "limit": 20}}'

# Step 2: 人群洞察（Port 5002）
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_audience_insight", "arguments": {"target_city": "广州", "product_desc": "高端白酒"}}'

# Step 3: 生成投放方案（Port 5003）
curl -X POST http://47.253.159.62:5003/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{"brand": "茅台", "budget": "50万", "city": "广州"}'

# Step 4: ROI计算（Port 5004）
curl -X POST http://47.253.159.62:5004/api/roi \
  -H "Content-Type: application/json" \
  -d '{"frames": 5000, "period_weeks": 2, "plan_type": "A"}'

# Step 5: 竞品监控（Port 5005）
curl http://47.253.159.62:5005/api/competitors

# Step 6: 创建投放计划（Port 5002）
curl -X POST http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_create_campaign", "arguments": {"name": "茅台-天河-周投", ...}}'
```

### 3.2 BabyAGI 自动化流程

```bash
# 使用 BabyAGI 自动完成上述6步
curl -X POST http://47.253.159.62:5006/api/task/add \
  -H "Content-Type: application/json" \
  -d '{"description": "生成茅台广州50万投放方案"}'

# BabyAGI 会自动：
# 1. 调用 Port 5002 查询点位
# 2. 调用 Port 5003 生成方案
# 3. 调用 Port 5004 计算ROI
# 4. 调用 Port 5005 查询竞品
# 5. 汇总结果返回
```

---

## 四、API 调用示例

### 4.1 Python SDK 封装

```python
import requests
from typing import Dict, List, Optional

class AIAdPlacerClient:
    """AIAdPlacer 统一客户端"""
    
    def __init__(self, base_urls: Dict[str, str]):
        self.mcp_url = base_urls.get("mcp", "http://47.253.159.62:5002")
        self.tom_url = base_urls.get("tom", "http://47.253.159.62:5003")
        self.roi_url = base_urls.get("roi", "http://47.253.159.62:5004")
        self.comp_url = base_urls.get("comp", "http://47.253.159.62:5005")
        self.baby_url = base_urls.get("baby", "http://47.253.159.62:5006")
    
    # ==================== MCP 工具调用 (Port 5002) ====================
    
    def call_mcp_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """调用 MCP 工具"""
        resp = requests.post(
            f"{self.mcp_url}/api/v2/mcp/pdooh/tools/call",
            json={"name": tool_name, "arguments": arguments}
        )
        return resp.json()
    
    def query_screens(self, city: str, district: Optional[str] = None, 
                      limit: int = 10) -> Dict:
        """查询智能屏点位"""
        return self.call_mcp_tool("pdooh_query_screens", {
            "city": city,
            "district": district,
            "limit": limit
        })
    
    def create_campaign(self, name: str, screen_ids: List[str], 
                       budget: float, start_date: str, end_date: str) -> Dict:
        """创建投放计划"""
        return self.call_mcp_tool("pdooh_create_campaign", {
            "name": name,
            "screen_ids": screen_ids,
            "budget": budget,
            "start_date": start_date,
            "end_date": end_date
        })
    
    # ==================== Tom Agent (Port 5003) ====================
    
    def generate_plan(self, brand: str, budget: str, city: str) -> Dict:
        """生成投放方案"""
        resp = requests.post(
            f"{self.tom_url}/api/plan/generate",
            json={"brand": brand, "budget": budget, "city": city}
        )
        return resp.json()
    
    def calc_cpm(self, screens: List[Dict], budget: float) -> Dict:
        """CPM 计算"""
        resp = requests.post(
            f"{self.tom_url}/api/cpm/calculate",
            json={"screens": screens, "budget": budget}
        )
        return resp.json()
    
    # ==================== ROI Agent (Port 5004) ====================
    
    def calc_roi(self, frames: int, period_weeks: int, 
                plan_type: str = "A") -> Dict:
        """ROI 计算"""
        resp = requests.post(
            f"{self.roi_url}/api/roi",
            json={"frames": frames, "period_weeks": period_weeks, "plan_type": plan_type}
        )
        return resp.json()
    
    # ==================== 竞品Agent (Port 5005) ====================
    
    def get_competitors(self) -> Dict:
        """获取竞品列表"""
        resp = requests.get(f"{self.comp_url}/api/competitors")
        return resp.json()
    
    def search_intelligence(self, keyword: str) -> Dict:
        """搜索市场情报"""
        resp = requests.get(f"{self.comp_url}/api/intelligence/search", 
                           params={"q": keyword})
        return resp.json()
    
    # ==================== BabyAGI (Port 5006) ====================
    
    def add_task(self, description: str) -> str:
        """添加任务，返回 task_id"""
        resp = requests.post(
            f"{self.baby_url}/api/task/add",
            json={"description": description}
        )
        return resp.json()["task"]["id"]
    
    def execute_task(self, task_id: str) -> Dict:
        """执行任务"""
        resp = requests.post(f"{self.baby_url}/api/task/execute/{task_id}")
        return resp.json()
    
    def run_workflow(self, descriptions: List[str]) -> List[Dict]:
        """执行工作流（多任务串联）"""
        results = []
        for desc in descriptions:
            task_id = self.add_task(desc)
            result = self.execute_task(task_id)
            results.append(result)
        return results


# ==================== 使用示例 ====================

client = AIAdPlacerClient({})

# 示例1：查询点位
screens = client.query_screens(city="广州", district="天河区", limit=10)
print(f"找到 {screens['count']} 个屏")

# 示例2：完整投放流程
plan = client.generate_plan(brand="茅台", budget="50万", city="广州")
roi = client.calc_roi(frames=5000, period_weeks=2, plan_type="A")
print(f"ROI: {roi['roi_percent']}%")

# 示例3：BabyAGI 自动化
tasks = [
    "查询广州单元门点位",
    "查询深圳门禁点位",
    "ROI计算 5000框两周"
]
results = client.run_workflow(tasks)
```

### 4.2 cURL 快速测试

```bash
# 健康检查（所有服务）
for port in 5002 5003 5004 5005 5006; do
  echo "=== Port $port ==="
  curl -s http://47.253.159.62:$port/health | python -m json.tool
done

# 完整流程测试
#!/bin/bash
BASE="http://47.253.159.62"

# 1. 查询点位
echo "=== 1. 查询点位 ==="
curl -X POST $BASE:5002/api/v2/mcp/pdooh/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "pdooh_query_screens", "arguments": {"city": "广州", "limit": 5}}' | python -m json.tool

# 2. 生成方案
echo "=== 2. 生成方案 ==="
curl -X POST $BASE:5003/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{"brand": "测试", "budget": "10万", "city": "广州"}' | python -m json.tool

# 3. ROI计算
echo "=== 3. ROI计算 ==="
curl -X POST $BASE:5004/api/roi \
  -H "Content-Type: application/json" \
  -d '{"frames": 1000, "period_weeks": 1, "plan_type": "A"}' | python -m json.tool

# 4. 竞品查询
echo "=== 4. 竞品查询 ==="
curl -s $BASE:5005/api/competitors | python -m json.tool

# 5. BabyAGI
echo "=== 5. BabyAGI ==="
curl -s $BASE:5006/api/demo | python -m json.tool
```

---

## 五、前端集成方案

### 5.1 Web 管理台调用流程

```javascript
// web/index.html 中的调用封装
class AIAdPlacerAPI {
  constructor(baseUrl = 'http://47.253.159.62:5002') {
    this.baseUrl = baseUrl;
  }

  // 调用 MCP 工具
  async callTool(toolName, args) {
    const resp = await fetch(`${this.baseUrl}/api/v2/mcp/pdooh/tools/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: toolName, arguments: args })
    });
    return resp.json();
  }

  // 查询点位
  async queryScreens(city, options = {}) {
    return this.callTool('pdooh_query_screens', { city, ...options });
  }

  // BabyAGI 任务提交
  async submitTask(description) {
    const resp = await fetch('http://47.253.159.62:5006/api/task/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description })
    });
    return resp.json();
  }
}

// 使用示例
const api = new AIAdPlacerAPI();
const screens = await api.queryScreens('广州', { district: '天河区', limit: 10 });
```

### 5.2 实时进度推送（WebSocket）

```javascript
// 连接后端 WebSocket
const ws = new WebSocket('ws://47.253.159.62:5002/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'task_progress') {
    updateProgressBar(data.progress);
  }
};

// 提交任务并监听进度
async function runTask(taskDesc) {
  ws.send(JSON.stringify({ action: 'submit_task', description: taskDesc }));
}
```

---

## 六、外部 AI Agent 集成

### 6.1 MCP 协议接入（AI-to-AI）

任何兼容 MCP 协议的 AI Agent 可直接调用 AIAdPlacer：

```yaml
# MCP Server 配置
name: AIAdPlacer
version: 2.0
endpoint: http://47.253.159.62:5002/api/v2/mcp/pdooh

tools:
  - name: pdooh_query_screens
    description: 查询智能屏点位
  - name: pdooh_create_campaign
    description: 创建投放计划
  # ... 共22个工具

# AI Agent 调用示例（Claude Desktop）
{
  "mcpServers": {
    "AIAdPlacer": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "http://47.253.159.62:5002/api/v2/mcp/pdooh/tools/call",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ]
    }
  }
}
```

### 6.2 LangChain 集成

```python
from langchain.agents import initialize_agent, Tool
from langchain.llms import Ollama

# 定义 AIAdPlacer 工具
tools = [
    Tool(
        name="QueryScreens",
        func=lambda q: client.query_screens(city=q),
        description="查询指定城市的智能屏点位"
    ),
    Tool(
        name="CreateCampaign",
        func=lambda q: client.create_campaign(**eval(q)),
        description="创建投放计划，参数：name, screen_ids, budget, start_date, end_date"
    )
]

# 初始化 Agent
llm = Ollama(model="qwen3.5:9b")
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# 执行任务
agent.run("帮我在广州天河区投放高端白酒广告，预算50万")
```

---

## 七、部署与运维

### 7.1 启动所有服务

```bash
#!/bin/bash
# start_all.sh - 启动所有微服务

# Port 5002: 主服务
cd /path/to/AIAdPlacer/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 5002 &

# Port 5003: Tom Agent
cd /path/to/AIAdPlacer/agents/tom_agent
python run.py --port 5003 &

# Port 5004: ROI Agent
cd /path/to/AIAdPlacer/agents/roi_agent
python run.py --port 5004 &

# Port 5005: 竞品Agent
cd /path/to/AIAdPlacer/agents/competitor_agent
python run.py --port 5005 &

# Port 5006: BabyAGI
cd /path/to/AIAdPlacer/agents/babyagi
python run.py --port 5006 &

echo "✅ 所有服务已启动"
```

### 7.2 健康检查脚本

```bash
#!/bin/bash
# health_check.sh - 检查所有服务健康状态

services=(
  "主服务:5002"
  "Tom Agent:5003"
  "ROI Agent:5004"
  "竞品Agent:5005"
  "BabyAGI:5006"
)

for service in "${services[@]}"; do
  name="${service%%:*}"
  port="${service##*:}"
  status=$(curl -s -o /dev/null -w "%{http_code}" http://47.253.159.62:$port/health)
  if [ "$status" = "200" ]; then
    echo "✅ $name (Port $port): 健康"
  else
    echo "❌ $name (Port $port): 异常 (HTTP $status)"
  fi
done
```

---

## 八、最佳实践

### 8.1 调用顺序建议

1. **点位查询** → 先确定投放范围
2. **人群洞察** → 了解目标受众
3. **方案生成** → 制定投放策略
4. **ROI计算** → 评估投资回报
5. **竞品分析** → 避开竞品高峰
6. **创建计划** → 执行投放

### 8.2 错误重试策略

```python
import time
from functools import wraps

def retry_on_error(max_retries=3, delay=1):
    """错误重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries - 1:
                        raise
                    time.sleep(delay * (i + 1))  # 指数退避
            return None
        return wrapper
    return decorator

@retry_on_error(max_retries=3)
def query_screens_safe(city):
    return client.query_screens(city)
```

### 8.3 并发调用优化

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

# 并发查询多个城市
cities = ["广州", "深圳", "东莞", "佛山"]

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(
        lambda city: client.query_screens(city, limit=10),
        cities
    ))

print(f"共查询 {sum(r['count'] for r in results)} 个屏")
```

---

## 九、常见问题

### Q1: 如何选择合适的端口？

- **单独功能调用**：直接调用对应端口（5003/5004/5005）
- **自动化流程**：使用 BabyAGI (5006) 自动编排
- **AI Agent 集成**：通过 MCP 协议调用 5002

### Q2: BabyAGI 支持哪些任务类型？

支持的任务类型由 `description` 关键词自动识别：
- 包含"查询" → 调用点位查询工具
- 包含"ROI" → 调用 ROI Agent
- 包含"方案" → 调用 Tom Agent

### Q3: 如何处理跨域问题？

所有服务已配置 CORS（`allow_origins=["*"]`），可直接从浏览器调用。

---

## 十、附录

### 附录A：完整 API 端点列表

| 端口 | 端点 | 方法 | 功能 |
|------|------|------|------|
| 5002 | `/api/v2/mcp/pdooh/tools/list` | GET | 列出22个工具 |
| 5002 | `/api/v2/mcp/pdooh/tools/call` | POST | 调用工具 |
| 5002 | `/api/v2/agents/execute` | POST | Agent编排 |
| 5003 | `/api/plan/generate` | POST | 生成方案 |
| 5003 | `/api/cpm/calculate` | POST | CPM计算 |
| 5004 | `/api/roi` | POST | ROI计算 |
| 5005 | `/api/competitors` | GET | 竞品列表 |
| 5006 | `/api/task/add` | POST | 添加任务 |
| 5006 | `/api/task/execute/<id>` | POST | 执行任务 |

### 附录B：错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查参数格式 |
| 404 | 资源不存在 | 检查ID是否正确 |
| 500 | 服务器内部错误 | 联系管理员 |
| 503 | 服务不可用 | 检查服务是否启动 |

---

**文档维护**：如有更新，请同步修改 `docs/platform-integration-plan.md`

> 📖 **相关文档**：
> - [`docs/babyagi-5006-guide.md`](docs/babyagi-5006-guide.md) - BabyAGI 完整使用指南
> - [`docs/mcp_api_guide.md`](docs/mcp_api_guide.md) - MCP API 完整文档
> - [`README.md`](README.md) - 项目主文档
