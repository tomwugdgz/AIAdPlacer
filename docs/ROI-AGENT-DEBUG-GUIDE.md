# ROI Agent 500 错误修复指南

## 问题描述

Tom Agent 调用 ROI Agent 时，返回 500 Internal Server Error。

**测试现象**：
- 用 TestClient 直接测试 ROI Agent → ✅ 200 OK
- 通过 httpx 调用 ROI Agent → ❌ 500 错误
- 用 curl 直接调用 ROI Agent → ❌ "Invalid HTTP request"

## 根本原因

**原因 1：URL 编码问题**
- `tom_agent.py` 的 `call_roi_agent` 函数直接拼接 URL 字符串
- 中文参数（如 `city=广州`）没有正确编码
- 修复：使用 `httpx` 的 `params` 参数（已修复）

**原因 2：ROI Agent 服务错误**
- ROI Agent 在处理某些请求时出错
- 需要查看错误日志，找到具体代码行

## 修复步骤

### 步骤 1：检查 ROI Agent 错误日志

**方法 A：前台启动 ROI Agent**
```bash
cd D:/Mirofish/AIAdPlacer/backend
python -m uvicorn app.roi_agent:router --host 0.0.0.0 --port 5004
```
- 发送请求，查看控制台输出的错误堆栈
- 找到具体出错的代码行

**方法 B：增加错误日志**
在 `roi_agent.py` 的 `/three-scenarios` 端点增加 try-except：
```python
@router.get("/three-scenarios")
async def get_three_scenarios(...):
    try:
        # 原有代码
        ...
    except Exception as e:
        import traceback
        logger.error(f"Error in get_three_scenarios: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
```

### 步骤 2：验证修复

**测试 1：ROI Agent 参数自动调整**
```bash
cd D:/Mirofish/AIAdPlacer/backend
python -c "
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.roi_agent import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# 测试有参数
resp = client.get('/api/v2/roi/three-scenarios?N=5000&cost=100000&T=14&city=广州&product=黑人牙膏')
print('Status:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print('Auto-adjusted:', data.get('auto_adjusted'))
    print('City tier:', data.get('city_tier'))
    print('Product type:', data.get('product_type'))
    for key, val in data['scenarios'].items():
        print(f'  {key}: ROI={val.get(\"roi_percent\")}%')
else:
    print('Error:', resp.text)
"
```

**测试 2：Tom Agent 联动功能**
```bash
cd D:/Mirofish/AIAdPlacer/backend
python -c "
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.tom_agent import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

# 测试生成投放方案（含 ROI 调用）
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
"
```

### 步骤 3：端口占用清理

如果遇到端口占用问题，运行：
```bash
# 查找占用端口的进程
netstat -ano | grep ":5004.*LISTEN"

# 杀掉进程
taskkill /F /PID <PID>
```

或者，使用 `run_all_agents.py` 一键启动所有 Agent（会自动检查端口占用）。

## 预期结果

修复后，Tom Agent 生成投放方案时，应自动调用 ROI Agent 计算三场景 ROI，并在响应中返回：
```json
{
  "plan_id": "PLAN-XXXX",
  "roi_result": {
    "scenarios": {
      "pessimistic": {"roi_percent": -21.69, ...},
      "neutral": {"roi_percent": 7.76, ...},
      "optimistic": {"roi_percent": 56.11, ...}
    },
    "auto_adjusted": true,
    "city_tier": "一线城市",
    "product_type": "日化"
  },
  "roi_visualization": "<div style=\"...\">...</div>"
}
```

## 联系支持

如果修复后仍有问题，请提供：
1. ROI Agent 错误日志（完整堆栈）
2. Tom Agent 错误日志（ROI Agent 调用失败信息）
3. 测试用例（输入参数、期望输出、实际输出）
