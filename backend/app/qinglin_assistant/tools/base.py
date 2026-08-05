"""青柠智能助手 — 工具抽象基类与上下文 / 结果容器。

工具（Tool）是助手可调用的原子能力单元：
- 知识库查询（真实 DB）
- 地图地理编码 / POI
- 沙箱命令执行
- 文档生成（skill）

每个工具实现 ``run(ctx) -> ToolResult``。编排层（api/routes、workflows）在
``check_permission`` 通过后调用工具，并对结果做字段脱敏。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolContext:
    """工具执行上下文。

    Attributes:
        role: 调用角色（建议传 ``Role`` 枚举或其字符串值）。
        session_id: 会话 ID（用于审计 / 记忆关联）。
        params: 意图识别产出的参数 dict。
        action: 当前动作（与 RBAC 对应）。
    """

    role: str
    session_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    action: str = ""


@dataclass
class ToolResult:
    """工具执行结果。

    Attributes:
        tool_name: 工具名（如 ``knowledge_base`` / ``map_geocode``）。
        success: 是否执行成功。
        content: 面向用户的文本摘要（会进入最终合成）。
        data: 结构化数据（真实 DB 结果 / 坐标 / 文件路径等）。
        demo: 是否为演示态（模拟操作）。
    """

    tool_name: str
    success: bool = True
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    demo: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool_name,
            "success": self.success,
            "content": self.content,
            "data": self.data,
            "demo": self.demo,
        }


class Tool(ABC):
    """工具抽象基类。"""

    name: str = "tool"
    description: str = ""

    @abstractmethod
    async def run(self, ctx: ToolContext) -> ToolResult:
        """执行工具逻辑，返回 ``ToolResult``。"""
        raise NotImplementedError
