"""
快速 API 测试脚本 - 验证所有 API 端点
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import tempfile
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

# 导入被测试的模块
from app.db_dao import DB_PATH as original_db_path
from app.db_api import db_api_router

# 创建临时数据库
db_fd, db_path_str = tempfile.mkstemp(suffix=".db")
db_path = Path(db_path_str)

conn = sqlite3.connect(str(db_path))
conn.execute("PRAGMA journal_mode=WAL")

# 创建测试表
conn.execute("""
    CREATE TABLE "单元门点位" (
        id INTEGER PRIMARY KEY,
        省份 TEXT,
        城市 TEXT,
        区域 TEXT,
        商圈 TEXT,
        楼盘类型 TEXT,
        楼栋数量 INTEGER,
        单元门数量 INTEGER,
        楼盘价格 REAL,
        住户数量 INTEGER,
        经度 REAL,
        纬度 REAL
    )
""")

conn.execute("""
    CREATE TABLE "客户通讯录" (
        id INTEGER PRIMARY KEY,
        客户简称 TEXT,
        品牌名称 TEXT,
        决策城市 TEXT,
        行业 TEXT,
        联系人 TEXT,
        手机 TEXT
    )
""")

# 插入测试数据
test_data = [
    (1, "广东省", "广州市", "天河区", "珠江新城", "住宅", 10, 20, 50000, 500, 113.3, 23.1),
    (2, "广东省", "广州市", "越秀区", "北京路", "住宅", 8, 16, 45000, 400, 113.2, 23.2),
    (3, "广东省", "深圳市", "南山区", "科技园", "商业", 15, 30, 80000, 800, 114.0, 22.5),
]

conn.executemany(
    'INSERT INTO "单元门点位" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    test_data
)

client_data = [
    (1, "华为技术", "华为", "深圳市", "通信", "张三", "13800138000"),
]

conn.executemany(
    'INSERT INTO "客户通讯录" VALUES (?, ?, ?, ?, ?, ?, ?)',
    client_data
)

conn.commit()
conn.close()

# 替换数据库路径
from app import db_dao as db_dao_module
db_dao_module.DB_PATH = db_path

# 创建测试应用
app = FastAPI()
app.include_router(db_api_router)

client = TestClient(app)

# 测试所有端点
print("=" * 60)
print("API 端点测试")
print("=" * 60)

# 1. 测试 GET /api/v2/db/tables
print("\n[测试 1] GET /api/v2/db/tables")
response = client.get("/api/v2/db/tables")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  成功: {data['success']}")
    print(f"  表数量: {data['total_tables']}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

# 2. 测试 GET /api/v2/db/<table_name>
print("\n[测试 2] GET /api/v2/db/单元门点位?page=1&page_size=2")
response = client.get("/api/v2/db/单元门点位?page=1&page_size=2")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  成功: {data['success']}")
    print(f"  返回记录数: {len(data['data'])}")
    print(f"  总记录数: {data['total']}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

# 3. 测试 GET /api/v2/db/stats/<table_name>
print("\n[测试 3] GET /api/v2/db/stats/单元门点位")
response = client.get("/api/v2/db/stats/单元门点位")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  成功: {data['success']}")
    print(f"  总记录数: {data['data']['total_count']}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

# 4. 测试 GET /api/v2/db/search/<table_name>
print("\n[测试 4] GET /api/v2/db/search/单元门点位?q=广州")
response = client.get("/api/v2/db/search/单元门点位?q=广州")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  成功: {data['success']}")
    print(f"  搜索结果数: {data['total']}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

# 5. 测试 GET /api/v2/db/clients/search
print("\n[测试 5] GET /api/v2/db/clients/search?keyword=华为")
response = client.get("/api/v2/db/clients/search?keyword=华为")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  成功: {data['success']}")
    print(f"  搜索结果数: {data['total']}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

# 6. 测试 GET /api/v2/db/points/<point_type>
print("\n[测试 6] GET /api/v2/db/points/unit_door?city=广州")
# Mock type_to_table
db_dao_module.type_to_table = {"unit_door": "单元门点位"}
response = client.get("/api/v2/db/points/unit_door?city=广州")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  成功: {data['success']}")
    print(f"  返回记录数: {data['total']}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

# 7. 测试 GET /api/v2/db/docs
print("\n[测试 7] GET /api/v2/db/docs")
response = client.get("/api/v2/db/docs")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  API 名称: {data['title']}")
    print(f"  端点数量: {len(data['endpoints'])}")
    print(f"  PASSED")
else:
    print(f"  FAILED: {response.text}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)

# 清理
os.close(db_fd)
os.unlink(str(db_path))

# 恢复原始路径
db_dao_module.DB_PATH = original_db_path
