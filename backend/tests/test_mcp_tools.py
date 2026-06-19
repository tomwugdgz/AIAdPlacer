"""
MCP Server 工具测试脚本

测试 app/pdooh_mcp.py 中的 MCP 工具
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.pdooh_mcp import router

# 创建测试应用
app = FastAPI()
app.include_router(router)

client = TestClient(app)

print("=" * 60)
print("MCP Server 工具测试")
print("=" * 60)

# 测试 1: 健康检查
print("\n[测试 1] 健康检查 - GET /api/v2/mcp/pdooh/health")
response = client.get("/api/v2/mcp/pdooh/health")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  服务: {data.get('service', 'N/A')}")
    print(f"  状态: {data.get('status', 'N/A')}")
    print(f"  版本: {data.get('version', 'N/A')}")
    print(f"  工具数量: {data.get('tools_count', 'N/A')}")
    
    if data.get("tools_count") == 22:
        print(f"  ✅ PASSED: tools_count = 22")
    else:
        print(f"  ❌ FAILED: 期望 22，实际 {data.get('tools_count')}")
else:
    print(f"  ❌ FAILED: {response.text}")

# 测试 2: 获取工具列表
print("\n[测试 2] 获取工具列表 - GET /api/v2/mcp/pdooh/tools/list")
response = client.get("/api/v2/mcp/pdooh/tools/list")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    tools = data.get("tools", [])
    print(f"  工具数量: {len(tools)}")
    
    # 检查是否有新增的 3 个工具
    new_tools = [
        "pdooh_query_pdooh_points",
        "pdooh_get_point_stats",
        "pdooh_search_clients"
    ]
    
    found_tools = []
    for tool in tools:
        if tool["name"] in new_tools:
            found_tools.append(tool["name"])
    
    print(f"  新增工具数量: {len(found_tools)}/3")
    for tool_name in found_tools:
        print(f"    ✅ {tool_name}")
    
    if len(found_tools) == 3:
        print(f"  ✅ PASSED: 3 个新增工具都已注册")
    else:
        missing = set(new_tools) - set(found_tools)
        print(f"  ❌ FAILED: 缺少工具 {missing}")
else:
    print(f"  ❌ FAILED: {response.text}")

# 测试 3: 调用工具 - pdooh_query_pdooh_points
print("\n[测试 3] 调用工具 - pdooh_query_pdooh_points")
tool_request = {
    "name": "pdooh_query_pdooh_points",
    "arguments": {
        "table_name": "单元门点位",
        "filters": {"city": "广州"},
        "page": 1,
        "page_size": 20
    }
}
response = client.post(
    "/api/v2/mcp/pdooh/tools/call",
    json=tool_request
)
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  调用成功: {data.get('success', 'N/A')}")
    print(f"  ✅ PASSED")
else:
    print(f"  ❌ FAILED: {response.text}")

# 测试 4: 调用工具 - pdooh_get_point_stats
print("\n[测试 4] 调用工具 - pdooh_get_point_stats")
tool_request = {
    "name": "pdooh_get_point_stats",
    "arguments": {
        "table_name": "单元门点位",
        "group_by": "city"
    }
}
response = client.post(
    "/api/v2/mcp/pdooh/tools/call",
    json=tool_request
)
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  调用成功: {data.get('success', 'N/A')}")
    print(f"  ✅ PASSED")
else:
    print(f"  ❌ FAILED: {response.text}")

# 测试 5: 调用工具 - pdooh_search_clients
print("\n[测试 5] 调用工具 - pdooh_search_clients")
tool_request = {
    "name": "pdooh_search_clients",
    "arguments": {
        "keyword": "华为",
        "limit": 10
    }
}
response = client.post(
    "/api/v2/mcp/pdooh/tools/call",
    json=tool_request
)
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"  调用成功: {data.get('success', 'N/A')}")
    print(f"  ✅ PASSED")
else:
    print(f"  ❌ FAILED: {response.text}")

# 测试 6: 获取 Skill YAML
print("\n[测试 6] 获取 Skill YAML - GET /api/v2/mcp/pdooh/skill.yaml")
response = client.get("/api/v2/mcp/pdooh/skill.yaml")
print(f"  状态码: {response.status_code}")
if response.status_code == 200:
    content = response.text
    print(f"  Skill YAML 长度: {len(content)} 字符")
    if "pdooh_query_screens" in content:
        print(f"  ✅ PASSED: Skill YAML 包含工具定义")
    else:
        print(f"  ❌ FAILED: Skill YAML 缺少工具定义")
else:
    print(f"  ❌ FAILED: {response.text}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
