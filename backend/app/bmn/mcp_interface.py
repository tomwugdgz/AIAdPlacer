"""
BMN MCP 接口（Model Context Protocol）
用于 Web4.0 AI 调用的标准化接口

MCP 是一个标准协议，允许 AI 模型调用外部工具。
本文件定义了 BMN 系统的 MCP 工具描述，让 AI 能够：
1. 获取品牌配置
2. 搜索资产金库
3. 执行工作流（生成文案）
4. 管理资产（增删改查）

使用方法：
- AI 模型读取本文件的 `mcp_tools` 定义
- 根据用户意图匹配对应的工具
- 调用对应的 BMN API 端点
- 返回结构化结果给 AI
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


# ── MCP 工具定义 ─────────────────────────────────────────────
# 这些定义告诉 AI 模型：有哪些工具可用、需要什么参数、返回什么

MCP_TOOLS = [
    {
        "name": "bmn_get_brand_config",
        "description": "获取品牌的完整配置信息（L1 品牌引擎）。包括品牌身份、核心价值、信任背书、差异化定位、Master Prompt。当用户询问品牌相关信息时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brand_name": {
                    "type": "string",
                    "description": "品牌名称，如：XX传媒、分众传媒、新潮传媒"
                }
            },
            "required": ["brand_name"]
        },
        "annotations": {
            "title": "获取品牌配置",
            "readOnlyHint": True,
            "destructiveHint": False
        }
    },
    {
        "name": "bmn_search_assets",
        "description": "语义检索资产金库（L2 数字资产金库）。根据关键词搜索相关营销资产（品牌诉求/产品卖点/用户场景/客户案例/行业知识/视觉资产/问答口径/风险边界）。支持 ChromaDB 向量搜索。当用户需要查找营销素材、案例、知识时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如：社区营销、到达率、差异化定位"
                },
                "asset_type": {
                    "type": "string",
                    "enum": [
                        "brand_appeal", "product_selling", "user_scenario",
                        "customer_case", "industry_knowledge", "visual_asset",
                        "qa_script", "risk_boundary", ""
                    ],
                    "description": "资产类型筛选（可选）。留空则搜索所有类型。"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回结果数量（默认 5）",
                    "default": 5
                }
            },
            "required": ["query"]
        },
        "annotations": {
            "title": "搜索资产金库",
            "readOnlyHint": True,
            "destructiveHint": False
        }
    },
    {
        "name": "bmn_run_case_study_workflow",
        "description": "执行客户案例生成工作流（L3 智能工作流）。输入原始素材，自动生成小红书文案、朋友圈文案、PPT 大纲，并进行合规检查。生成的文案会自动保存到资产金库。当用户需要生成营销文案、案例分享、提案大纲时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_material": {
                    "type": "string",
                    "description": "原始素材（必填），包括品牌/产品信息、数据、卖点等。如：XX传媒社区媒体资源，覆盖70000+小区，开门App 600万+DAU，单元门灯箱日均到达率87%"
                },
                "client_name": {
                    "type": "string",
                    "description": "客户名称（必填），如：某日化品牌、某药店连锁"
                },
                "industry": {
                    "type": "string",
                    "description": "行业（可选），如：日化、药店、家电、快消"
                },
                "product_info": {
                    "type": "string",
                    "description": "产品信息（可选），如：新品洗发水社区推广"
                }
            },
            "required": ["raw_material", "client_name"]
        },
        "annotations": {
            "title": "执行案例生成工作流",
            "readOnlyHint": False,
            "destructiveHint": False
        }
    },
    {
        "name": "bmn_list_assets",
        "description": "列出资产金库中的所有资产（支持分页和筛选）。当用户需要浏览所有可用资产时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_type": {
                    "type": "string",
                    "description": "资产类型筛选（可选）"
                },
                "keyword": {
                    "type": "string",
                    "description": "关键词搜索（可选）"
                },
                "page": {
                    "type": "integer",
                    "description": "页码（默认 1）",
                    "default": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页数量（默认 20）",
                    "default": 20
                }
            },
            "required": []
        },
        "annotations": {
            "title": "列出资产",
            "readOnlyHint": True,
            "destructiveHint": False
        }
    },
    {
        "name": "bmn_get_workflow_run",
        "description": "查询工作流运行记录详情。获取之前执行的工作流结果。当用户需要查看历史工作流记录时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "工作流运行 ID（从 run_case_study_workflow 返回的 workflow_run_id）"
                }
            },
            "required": ["run_id"]
        },
        "annotations": {
            "title": "查询工作流记录",
            "readOnlyHint": True,
            "destructiveHint": False
        }
    }
]


# ── MCP 工具执行器 ─────────────────────────────────────────────
# AI 模型选择工具后，调用对应的 BMN API

class BmnMcpExecutor:
    """执行 BMN MCP 工具"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5003"):
        self.base_url = base_url.rstrip('/')
    
    def execute(self, tool_name: str, arguments: Dict) -> Dict:
        """
        执行 MCP 工具
        :param tool_name: 工具名称（如 bmn_get_brand_config）
        :param arguments: 工具参数（dict）
        :return: {"content": [...], "isError": bool}
        """
        try:
            if tool_name == "bmn_get_brand_config":
                return self._get_brand_config(arguments)
            elif tool_name == "bmn_search_assets":
                return self._search_assets(arguments)
            elif tool_name == "bmn_run_case_study_workflow":
                return self._run_case_study_workflow(arguments)
            elif tool_name == "bmn_list_assets":
                return self._list_assets(arguments)
            elif tool_name == "bmn_get_workflow_run":
                return self._get_workflow_run(arguments)
            else:
                return {
                    "content": [{"type": "text", "text": f"未知工具：{tool_name}"}],
                    "isError": True
                }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"执行失败：{str(e)}"}],
                "isError": True
            }
    
    def _get_brand_config(self, args: Dict) -> Dict:
        import requests
        brand_name = args["brand_name"]
        url = f"{self.base_url}/api/v2/bmn/brand/config?brand_name={requests.utils.quote(brand_name)}"
        resp = requests.get(url)
        data = resp.json()
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""## {data.get('brand_name', brand_name)} — 品牌配置

### 品牌身份
{data.get('identity', '-')}

### 核心价值
{data.get('value_proposition', '-')}

### 差异化定位
{data.get('differentiation', '-')}

### 信任背书
{chr(10).join(['✅ ' + p for p in data.get('trust_proof', [])])}

### Master Prompt（供 AI 调用）
{data.get('master_prompt', '-')}
"""
                }
            ],
            "isError": False
        }
    
    def _search_assets(self, args: Dict) -> Dict:
        import requests
        url = f"{self.base_url}/api/v2/bmn/assets/search"
        payload = {
            "query": args["query"],
            "asset_type": args.get("asset_type", ""),
            "top_k": args.get("top_k", 5)
        }
        resp = requests.post(url, json=payload)
        data = resp.json()
        
        results = data.get("results", [])
        if not results:
            text = "未找到相关资产。"
        else:
            lines = [f"## 找到 {len(results)} 条相关资产：\n"]
            for i, r in enumerate(results, 1):
                meta = r.get("metadata", {})
                score = r.get("relevance_score", 0)
                lines.append(f"{i}. **{meta.get('title', '-')}** （相关度：{score:.2f}）")
                lines.append(f"   - 类型：{meta.get('asset_type', '-')}")
                lines.append(f"   - 内容预览：{r.get('content', '')[:100]}...")
                if r.get("asset"):
                    lines.append(f"   - 使用次数：{r['asset'].get('usage_count', 0)}")
                lines.append("")
            text = "\n".join(lines)
        
        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }
    
    def _run_case_study_workflow(self, args: Dict) -> Dict:
        import requests
        url = f"{self.base_url}/api/v2/bmn/workflows/case_study/run"
        payload = {
            "raw_material": args["raw_material"],
            "client_name": args["client_name"],
            "industry": args.get("industry", ""),
            "product_info": args.get("product_info", "")
        }
        resp = requests.post(url, json=payload)
        data = resp.json()
        
        if not data.get("ok"):
            return {
                "content": [{"type": "text", "text": f"工作流执行失败：{data.get('detail', '未知错误')}"}],
                "isError": True
            }
        
        result = data.get("result", {})
        copies = result.get("copies", {})
        compliance = data.get("compliance", [])
        
        lines = [f"## ✅ 工作流执行成功（ID：{data.get('workflow_run_id', '-')}）\n"]
        
        if copies:
            lines.append("### 生成文案：\n")
            if copies.get("xhs"):
                lines.append(f"**小红书文案：**\n{copies['xhs']}\n")
            if copies.get("moments"):
                lines.append(f"**朋友圈文案：**\n{copies['moments']}\n")
            if copies.get("ppt_outline"):
                lines.append(f"**PPT 大纲：**\n{copies['ppt_outline']}\n")
        
        if compliance:
            lines.append("### ⚠️ 合规检查：\n")
            for c in compliance:
                lines.append(f"- {c}\n")
        
        if result.get("asset_saved"):
            lines.append(f"✅ 生成的文案已保存到资产金库（资产 ID：{result.get('asset_id', '-')}）\n")
        
        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "isError": False
        }
    
    def _list_assets(self, args: Dict) -> Dict:
        import requests
        url = f"{self.base_url}/api/v2/bmn/assets"
        params = {}
        if args.get("asset_type"):
            params["asset_type"] = args["asset_type"]
        if args.get("keyword"):
            params["keyword"] = args["keyword"]
        params["page"] = args.get("page", 1)
        params["page_size"] = args.get("page_size", 20)
        
        resp = requests.get(url, params=params)
        data = resp.json()
        
        items = data.get("items", [])
        if not items:
            text = "暂无资产数据。"
        else:
            type_map = {
                "brand_appeal": "品牌诉求",
                "product_selling": "产品卖点",
                "user_scenario": "用户场景",
                "customer_case": "客户案例",
                "industry_knowledge": "行业知识",
                "visual_asset": "视觉资产",
                "qa_script": "问答口径",
                "risk_boundary": "风险边界"
            }
            lines = [f"## 资产列表（共 {data.get('total', 0)} 条）：\n"]
            for item in items:
                lines.append(f"- **{item.get('title', '-')}** （{type_map.get(item.get('asset_type'), item.get('asset_type'))}）")
                lines.append(f"  - 标签：{', '.join(item.get('tags', []))}")
                lines.append(f"  - 使用次数：{item.get('usage_count', 0)}")
                lines.append("")
            text = "\n".join(lines)
        
        return {
            "content": [{"type": "text", "text": text}],
            "isError": False
        }
    
    def _get_workflow_run(self, args: Dict) -> Dict:
        import requests
        run_id = args["run_id"]
        url = f"{self.base_url}/api/v2/bmn/workflows/runs/{run_id}"
        resp = requests.get(url)
        data = resp.json()
        
        lines = [f"## 工作流运行记录（{run_id}）\n"]
        lines.append(f"- **工作流名称：** {data.get('workflow_name', '-')}")
        lines.append(f"- **状态：** {data.get('status', '-')}")
        lines.append(f"- **创建时间：** {data.get('created_at', '-')}")
        lines.append(f"- **完成时间：** {data.get('finished_at', '-')}")
        
        output = data.get("output_data")
        if output:
            lines.append(f"\n### 输出结果：\n{output}")
        
        error = data.get("error_msg")
        if error:
            lines.append(f"\n### ❌ 错误信息：\n{error}")
        
        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "isError": False
        }


# ── MCP 服务器接口 ─────────────────────────────────────────────
# 用于 Web4.0 AI 调用（返回 MCP 标准格式）

def mcp_list_tools() -> Dict:
    """
    MCP 标准接口：列出所有可用工具
    对应 MCP 协议的 `tools/list` 请求
    """
    return {
        "tools": MCP_TOOLS
    }


def mcp_call_tool(tool_name: str, arguments: Dict) -> Dict:
    """
    MCP 标准接口：调用工具
    对应 MCP 协议的 `tools/call` 请求
    
    :param tool_name: 工具名称
    :param arguments: 工具参数（JSON 对象）
    :return: MCP 标准响应格式
    """
    executor = BmnMcpExecutor()
    return executor.execute(tool_name, arguments)


# ── FastAPI HTTP 接口（用于 Web4.0 调用）─────────────────────────
# 如果你的 Web4.0 系统支持 HTTP MCP，可以直接调用这些端点

try:
    from fastapi import APIRouter
    
    mcp_router = APIRouter()
    
    @mcp_router.get("/mcp/tools")
    async def list_mcp_tools():
        """MCP 标准：列出所有工具"""
        return mcp_list_tools()
    
    @mcp_router.post("/mcp/tools/call")
    async def call_mcp_tool(body: Dict):
        """MCP 标准：调用工具"""
        tool_name = body.get("name")
        arguments = body.get("arguments", {})
        if not tool_name:
            return {"error": "缺少工具名称"}
        return mcp_call_tool(tool_name, arguments)
    
    # 将 mcp_router 注册到主应用
    app.include_router(mcp_router, prefix="/api/v2/bmn")
    
except ImportError:
    mcp_router = None


if __name__ == "__main__":
    # 测试 MCP 工具
    import json
    
    print("=" * 60)
    print("BMN MCP 接口测试")
    print("=" * 60)
    
    executor = BmnMcpExecutor()
    
    # 测试 1：获取品牌配置
    print("\n[测试 1] 获取品牌配置...")
    result = executor.execute("bmn_get_brand_config", {"brand_name": "XX传媒"})
    print(result["content"][0]["text"][:500])
    
    # 测试 2：搜索资产
    print("\n\n[测试 2] 搜索资产...")
    result = executor.execute("bmn_search_assets", {"query": "社区营销", "top_k": 2})
    print(result["content"][0]["text"][:500])
    
    print("\n" + "=" * 60)
    print("MCP 接口测试完成")
    print("=" * 60)
