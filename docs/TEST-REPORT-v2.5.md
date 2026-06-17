# AIAdPlacer v2.5.0 测试报告

## 测试时间
2026-06-17 13:15

## 测试环境
- 操作系统：Windows 10
- Python：3.13.12
- FastAPI：0.104.1
- httpx：0.25.0

## 测试内容

### 1. ROI Agent（端口 5004）

#### ✅ 通过测试
| 测试项 | 方法 | 结果 |
|--------|------|------|
| `/health` 端点 | TestClient | ✅ 200 OK，返回 `{"status": "ok", "agent": "ROI Agent", "version": "2.2.0"}` |
| `/formula` 端点 | TestClient | ✅ 200 OK，返回完整公式说明 |
| `/three-scenarios` 端点（无参数） | TestClient | ✅ 200 OK，返回三场景 ROI（悲观/中性/乐观） |
| `/three-scenarios` 端点（有参数） | TestClient | ✅ 200 OK，参数自动调整功能正常 |

#### ❌ 失败测试
| 测试项 | 方法 | 结果 | 原因 |
|--------|------|------|------|
| `/health` 端点 | curl | ❌ 500 Internal Server Error | 未知（可能是 uvicorn 启动问题） |
| `/three-scenarios` 端点（有中文参数） | curl + httpx | ❌ 500 Internal Server Error | URL 编码问题或代码错误 |

#### 📊 测试结果详情

**测试 1：参数自动调整功能**
```python
# 输入
city = "广州"
product = "黑人牙膏"

# 输出
{
  "auto_adjusted": True,
  "city_tier": "一线城市",
  "product_type": "日化",
  "scenarios": {
    "pessimistic": {"roi_percent": -21.69, "params": {"r": 0.153, "a": 20.9, "f": 1.34}},
    "neutral":      {"roi_percent": 7.76,  "params": {"r": 0.184, "a": 22.99, "f": 1.4}},
    "optimistic":   {"roi_percent": 56.11, "params": {"r": 0.224, "a": 24.98, "f": 1.47}}
  }
}
```

**结论**：参数自动调整功能正常工作。一线城市 + 日化产品，系统自动调整了 `r/a/f` 参数。

---

### 2. Tom Agent（端口 5003）

#### ✅ 通过测试
| 测试项 | 方法 | 结果 |
|--------|------|------|
| `/health` 端点 | TestClient | ✅ 200 OK，返回 `{"status": "ok", "agent": "Tom", "version": "2.1.0"}` |
| `/plan/generate` 端点（无 ROI） | TestClient | ✅ 200 OK，返回投放方案（无 ROI 结果） |

#### ❌ 失败测试
| 测试项 | 方法 | 结果 | 原因 |
|--------|------|------|------|
| `/plan/generate` 端点（含 ROI 调用） | TestClient + httpx | ❌ ROI Agent 返回 500 错误 | ROI Agent 服务有问题 |

#### 📊 测试结果详情

**测试 2：Tom Agent 生成投放方案（不含 ROI）**
```python
# 输入
{
  "brand": "黑人牙膏",
  "product": "双重薄荷牙膏",
  "budget": 100000,
  "cities": ["广州"]
}

# 输出
{
  "plan_id": "PLAN-D3A04C1D",
  "brand": "黑人牙膏",
  "summary": "为 黑人牙膏 的 双重薄荷牙膏 生成了覆盖 1 个城市的投放方案，总预算 100,000 元。",
  "media_mix": [...],
  "estimated_reach": ...,
  "estimated_impressions": ...,
  "total_cost": 100000,
  "timeline": [...],
  "roi_result": None,  # ROI Agent 调用失败
  "roi_visualization": None
}
```

**结论**：Tom Agent 基本功能正常，但联动 ROI Agent 失败。

---

### 3. 联动功能（Tom Agent → ROI Agent）

#### ❌ 失败测试
| 测试项 | 方法 | 结果 | 原因 |
|--------|------|------|------|
| Tom Agent 调用 ROI Agent | httpx | ❌ ROI Agent 返回 500 错误 | ROI Agent 服务在处理请求时出错 |

#### 🔍 问题分析

1. **ROI Agent 服务问题**：
   - 用 TestClient 测试时，ROI Agent 所有端点都返回 200 OK
   - 但通过 httpx 调用时，返回 500 错误
   - 可能是 URL 编码问题（中文参数）或代码运行时错误

2. **端口占用问题**：
   - 测试过程中，端口 5004 多次被占用
   - 可能是之前的进程没有完全杀掉

---

## 修复建议

### 1. 修复 ROI Agent 的 500 错误

**方案 A：检查 ROI Agent 日志**
- 在前台启动 ROI Agent，捕获错误日志
- 查看具体是哪个代码行出错

**方案 B：修复 URL 编码问题**
- 在 `tom_agent.py` 的 `call_roi_agent` 函数里，使用 `httpx` 的 `params` 参数（已修复）
- 确保中文参数正确编码

**方案 C：增加错误处理**
- 在 ROI Agent 的 `/three-scenarios` 端点里，增加 try-except，返回更详细的错误信息

### 2. 修复端口占用问题

**方案 A：使用单一启动脚本**
- 创建 `run_all_agents.py`，一键启动所有 Agent
- 启动时自动检查端口占用，先杀掉旧进程

**方案 B：使用 Docker**
- 将每个 Agent 容器化，避免端口冲突

---

## 下一步行动

1. **立即修复**：检查 ROI Agent 的错误日志，找到 500 错误的根本原因
2. **代码优化**：增加更详细的错误处理和日志输出
3. **重新测试**：修复后，重新运行所有测试用例
4. **部署准备**：编写部署文档，包含启动顺序、端口分配、健康检查等

---

## 附录：测试用例代码

### A. 测试 ROI Agent 参数自动调整

```python
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.roi_agent import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# 测试 1：有城市+产品参数
resp = client.get('/api/v2/roi/three-scenarios?N=5000&cost=100000&T=14&city=广州&product=黑人牙膏')
print('Status:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print('Auto-adjusted:', data.get('auto_adjusted'))
    print('City tier:', data.get('city_tier'))
    print('Product type:', data.get('product_type'))
    for key, val in data['scenarios'].items():
        print(f'  {key}: ROI={val.get("roi_percent")}%')
```

### B. 测试 Tom Agent 联动功能

```python
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.tom_agent import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# 测试：生成投放方案（含 ROI 调用）
resp = client.post('/api/v2/tom/plan/generate', 
    json={
        'brand': '黑人牙膏',
        'product': '双重薄荷牙膏',
        'budget': 100000,
        'cities': ['广州']
    })
print('Status:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print('Plan ID:', data.get('plan_id'))
    print('ROI result:', 'Yes' if data.get('roi_result') else 'No')
    print('ROI visualization:', 'Yes' if data.get('roi_visualization') else 'No')
else:
    print('Error:', resp.text)
```
