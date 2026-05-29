"""
测试 BMN 所有接口
"""
import urllib.request
import urllib.parse
import json
import time
import sys

BASE = "http://127.0.0.1:5003"
TIMEOUT = 15

def get(path):
    url = BASE + path
    try:
        r = urllib.request.urlopen(url, timeout=TIMEOUT)
        return r.status, r.read().decode("utf-8")
    except Exception as e:
        return None, str(e)

def post(path, data):
    url = BASE + path
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        r = urllib.request.urlopen(req, timeout=TIMEOUT)
        return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return None, str(e)

# ── 等待服务就绪 ──────────────────────────────────────
print("等待 BMN 服务就绪...")
for i in range(20):
    status, _ = get("/")
    if status == 200:
        print("✅ 服务已就绪")
        break
    time.sleep(1)
else:
    print("❌ 服务未启动，请先运行：")
    print("  cd D:/Mirofish/AIAdPlacer/backend")
    print("  D:/Mirofish/AIAdPlacer/backend/venv/Scripts/python.exe -m uvicorn app.bmn_app:app --host 127.0.0.1 --port 5003")
    sys.exit(1)

# ── 测试 1：根路径 ────────────────────────────────────
print("\n[1] 测试根路径 /")
status, body = get("/")
print(f"  status={status}")
print(f"  body={body[:100]}")

# ── 测试 2：获取品牌配置 ──────────────────────────────
print("\n[2] 测试 GET /api/v2/bmn/brand/config?brand_name=XX传媒")
path = "/api/v2/bmn/brand/config?" + urllib.parse.urlencode({"brand_name": "XX传媒"})
status, body = get(path)
print(f"  status={status}")
print(f"  body={body[:300]}")

# ── 测试 3：获取母指令 ──────────────────────────────
print("\n[3] 测试 GET /api/v2/bmn/brand/master_prompt?brand_name=XX传媒")
path = "/api/v2/bmn/brand/master_prompt?" + urllib.parse.urlencode({"brand_name": "XX传媒"})
status, body = get(path)
print(f"  status={status}")
print(f"  body={body[:300]}")

# ── 测试 4：资产列表 ──────────────────────────────
print("\n[4] 测试 GET /api/v2/bmn/assets?asset_type=product_selling")
status, body = get("/api/v2/bmn/assets?asset_type=product_selling&page=1&page_size=5")
print(f"  status={status}")
print(f"  body={body[:300]}")

# ── 测试 5：资产搜索 ──────────────────────────────
print("\n[5] 测试 POST /api/v2/bmn/assets/search")
status, body = post("/api/v2/bmn/assets/search", {"query": "单元门灯箱 到达率", "top_k": 3})
print(f"  status={status}")
print(f"  body={body[:300]}")

print("\n─── 测试完成 ───")
